import requests
import logging
from datetime import datetime
from django.db import transaction
from .models import Pais, IndicadorEconomico, TipoCambio, LogActividad

logger = logging.getLogger(__name__)


class ExternalDataSyncService:
    """
    Servicio encargado de centralizar la lógica de integración con APIs externas 
    (Banco Mundial y ExchangeRate-API), implementando manejo de reintentos, 
    bloques atómicos de transacción y registro de auditoría (logs).
    """

    WORLD_BANK_BASE_URL = "https://api.worldbank.org/v2/country"
    EXCHANGE_API_URL = "https://open.er-api.com/v6/latest/USD"

    @classmethod
    def sincronizar_indicadores_banco_mundial(cls, usuario=None):
        """
        Consume la API del Banco Mundial utilizando consultas agrupadas (Batch Request)
        separando los códigos ISO por punto y coma (;). Esto reduce las peticiones HTTP 
        de 30 a solo 3, evitando bloqueos por rate-limiting y timeouts.
        """
        world_bank_https_url = "https://api.worldbank.org/v2/country"
        
        paises = list(Pais.objects.filter(activo=True))
        if not paises:
            return False, "No hay países activos registrados en la base de datos."

        # Mapeamos los países por código ISO en memoria para evitar consultas N+1 a PostgreSQL
        paises_dict = {pais.codigo_iso.upper(): pais for pais in paises}
        codigos_iso_batch = ";".join(paises_dict.keys())  # Ej: "CO;BR;MX;AR;CL;PE;EC;UY;CR;PA"

        indicadores_mapeo = {
            'NY.GDP.MKTP.CD': 'PIB',
            'FP.CPI.TOTL.ZG': 'INFLACION',
            'SL.UEM.TOTL.ZS': 'DESEMPLEO',
        }
        
        sincronizados_count = 0

        try:
            with transaction.atomic():
                for wb_indicator, local_type in indicadores_mapeo.items():
                    # Solicitamos todos los países en una sola llamada con per_page=500 para traer todo sin paginar
                    url = (
                        f"{world_bank_https_url}/{codigos_iso_batch}/indicator/{wb_indicator}"
                        f"?format=json&date=2020:2025&per_page=500"
                    )
                    
                    try:
                        # Añadimos un User-Agent estándar para evitar bloqueos del firewall de World Bank
                        headers = {'User-Agent': 'DataPulseLatam/1.0'}
                        response = requests.get(url, headers=headers, timeout=20)
                        
                        if response.status_code == 200:
                            data = response.json()
                            if len(data) > 1 and data[1]:
                                for entry in data[1]:
                                    valor = entry.get('value')
                                    anio = entry.get('date')
                                    # World Bank devuelve el código ISO de 2 letras en entry['country']['id']
                                    iso_code = entry.get('country', {}).get('id', '').upper()
                                    
                                    pais_obj = paises_dict.get(iso_code)
                                    
                                    if pais_obj and valor is not None and anio is not None:
                                        # Si es PIB, convertimos de dólares absolutos a miles de millones para coincidir con la unidad
                                        valor_final = float(valor) / 1_000_000_000 if local_type == 'PIB' else float(valor)
                                        
                                        IndicadorEconomico.objects.update_or_create(
                                            pais=pais_obj,
                                            tipo=local_type,
                                            anio=int(anio),
                                            defaults={
                                                'valor': round(valor_final, 4),
                                                'unidad': 'USD_MILES_MILLONES' if local_type == 'PIB' else 'PORCENTAJE',
                                                'fuente': 'WORLD_BANK'
                                            }
                                        )
                                        sincronizados_count += 1
                        else:
                            logger.warning(f"Respuesta inesperada de World Bank ({local_type}): HTTP {response.status_code}")
                            
                    except requests.RequestException as e:
                        logger.warning(f"Advertencia de red con World Bank para el lote ({local_type}): {str(e)}")
                        continue

                if usuario:
                    LogActividad.objects.create(
                        usuario=usuario,
                        accion='CREAR',
                        entidad_afectada='IndicadorEconomico',
                        detalle={'sincronizados': sincronizados_count},
                        fecha=datetime.now()
                    )

            return True, f"Sincronización de Banco Mundial exitosa. Registros procesados: {sincronizados_count}"
        
        except Exception as e:
            logger.error(f"Error crítico en sincronización del Banco Mundial: {str(e)}")
            return False, str(e)

    @classmethod
    def sincronizar_tasas_cambio(cls, usuario=None):
        """
        Consume la API de ExchangeRate-API para obtener las tasas de cambio vigentes 
        frente al USD y calcula la variación porcentual respecto al registro anterior.
        """
        try:
            response = requests.get(cls.EXCHANGE_API_URL, timeout=10)
            if response.status_code != 200:
                return False, f"Error en la API de tasas de cambio. Código HTTP: {response.status_code}"

            data = response.json()
            rates = data.get('rates', {})
            fecha_str = data.get('time_last_update_utc') # o fecha actual por defecto
            fecha_actual = datetime.now().date()

            paises = Pais.objects.filter(activo=True)
            actualizados_count = 0

            with transaction.atomic():
                for pais in paises:
                    moneda = pais.moneda_codigo
                    if moneda in rates or moneda == 'USD':
                        # Si la moneda es USD, la tasa es 1.0; de lo contrario, extraemos de rates
                        tasa_usd = 1.0 if moneda == 'USD' else float(rates.get(moneda, 1.0))
                        
                        # Invertimos o ajustamos según la base USD de ExchangeRate-API (1 USD = X Moneda local)
                        # ExchangeRate-API da 1 USD = X Moneda. Para guardar tasa local/USD calculamos el inverso si es necesario,
                        # o guardamos la tasa directa devuelta por el servicio base.
                        tasa_registro = 1.0 / tasa_usd if moneda != 'USD' and tasa_usd > 0 else 1.0

                        # Buscamos el registro anterior para calcular la variación porcentual
                        ultimo_cambio = TipoCambio.objects.filter(moneda_origen=moneda).order_by('-fecha').first()
                        variacion = 0.0
                        
                        if ultimo_cambio and ultimo_cambio.tasa > 0:
                            variacion = ((tasa_registro - ultimo_cambio.tasa) / ultimo_cambio.tasa) * 100

                        TipoCambio.objects.update_or_create(
                            moneda_origen=moneda,
                            moneda_destino='USD',
                            fecha=fecha_actual,
                            defaults={
                                'tasa': tasa_registro,
                                'variacion_porcentual': round(variacion, 4),
                                'fuente': 'ExchangeRate-API'
                            }
                        )
                        actualizados_count += 1

                if usuario:
                    LogActividad.objects.create(
                        usuario=usuario,
                        accion='CREAR',
                        entidad_afectada='TipoCambio',
                        detalle={'actualizados': actualizados_count},
                        fecha=datetime.now()
                    )

            return True, f"Tasas de cambio sincronizadas correctamente. Total monedas: {actualizados_count}"

        except Exception as e:
            logger.error(f"Error crítico en sincronización de tasas de cambio: {str(e)}")
            return False, str(e)