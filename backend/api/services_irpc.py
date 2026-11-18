import logging
from datetime import datetime, timedelta
import statistics
from django.db import transaction
from .models import Pais, IndicadorEconomico, TipoCambio, IndiceRiesgo, Alerta, LogActividad

logger = logging.getLogger(__name__)


class IRPCService:
    """
    Servicio encargado del cálculo automatizado del Índice de Riesgo País Compuesto (IRPC)
    y de la generación proactiva de alertas según las reglas de negocio de DataPulse Latam.
    """

    @classmethod
    def calcular_todos_los_paises(cls, usuario=None):
        """
        Recalcula el IRPC para todos los países activos registrados en el sistema,
        aplicando la ponderación analítica y registrando la trazabilidad de auditoría.
        """
        paises = Pais.objects.filter(activo=True)
        resultados_count = 0
        
        with transaction.atomic():
            for pais in paises:
                try:
                    cls._calcular_y_guardar_irpc_pais(pais)
                    resultados_count += 1
                except Exception as e:
                    logger.error(f"Error crítico calculando IRPC para el país {pais.codigo_iso}: {str(e)}")

            # Registro de auditoría institucional
            if usuario:
                LogActividad.objects.create(
                    usuario=usuario,
                    accion='CREAR',
                    entidad_afectada='IndiceRiesgo',
                    detalle={'paises_calculados': resultados_count},
                )

        return True, f"Cálculo de IRPC finalizado correctamente para {resultados_count} países."

    @classmethod
    def _calcular_y_guardar_irpc_pais(cls, pais):
        """
        Ejecuta el pipeline de cálculo para un país específico:
        1. Recupera el historial previo para detección de variaciones drásticas.
        2. Calcula los tres scores parciales (Económico, Cambiario, Estabilidad).
        3. Aplica la fórmula ponderada global y determina la categoría de riesgo.
        4. Evalúa disparadores para la creación automática de Alertas.
        """
        ultimo_registro = IndiceRiesgo.objects.filter(pais=pais).order_by('-fecha_calculo').first()
        irpc_anterior = ultimo_registro.indice_compuesto if ultimo_registro else None

        # 1. Cálculo de Scores parciales con sus desgloses detallados
        score_eco, detalle_eco = cls._calcular_score_economico(pais)
        score_camb, detalle_camb = cls._calcular_score_cambiario(pais)
        score_est, detalle_est = cls._calcular_score_estabilidad(pais)

        # 2. Aplicación de la fórmula ponderada del IRPC (40% Eco, 30% Cambiario, 30% Estabilidad)
        indice_compuesto = round((score_eco * 0.40) + (score_camb * 0.30) + (score_est * 0.30), 2)

        # 3. Clasificación del Nivel de Riesgo según umbrales institucionales
        if indice_compuesto >= 75:
            nivel = 'BAJO'
        elif indice_compuesto >= 50:
            nivel = 'MODERADO'
        elif indice_compuesto >= 25:
            nivel = 'ALTO'
        else:
            nivel = 'CRITICO'

        detalle_completo = {
            'economico': detalle_eco,
            'cambiario': detalle_camb,
            'estabilidad': detalle_est,
            'ponderaciones': {'eco': 0.40, 'camb': 0.30, 'est': 0.30}
        }

        # Persistencia del nuevo índice calculado
        nuevo_indice = IndiceRiesgo.objects.create(
            pais=pais,
            score_economico=score_eco,
            score_cambiario=score_camb,
            score_estabilidad=score_est,
            indice_compuesto=indice_compuesto,
            nivel_riesgo=nivel,
            detalle_calculo=detalle_completo
        )

        # 4. Evaluación de reglas de negocio para alertas proactivas
        cls._evaluar_alertas(pais, nuevo_indice, irpc_anterior, detalle_eco)

    @staticmethod
    def _obtener_ultimo_indicador(pais, tipo):
        """Método auxiliar para recuperar el valor más reciente de un indicador por año."""
        ind = IndicadorEconomico.objects.filter(pais=pais, tipo=tipo).order_by('-anio').first()
        return ind.valor if ind else None

    @staticmethod
    def _obtener_indicador_por_anio(pais, tipo, anio):
        """Método auxiliar para recuperar un indicador en un año específico."""
        ind = IndicadorEconomico.objects.filter(pais=pais, tipo=tipo, anio=anio).first()
        return ind.valor if ind else None

    @classmethod
    def _calcular_score_economico(cls, pais):
        """
        Calcula el Score Económico (0-100) evaluando PIB per cápita, inflación, desempleo y deuda/PIB.
        """
        score = 100
        penalizaciones = {}

        # Evaluación de PIB per cápita
        pib_pc = cls._obtener_ultimo_indicador(pais, 'PIB_PERCAPITA')
        if pib_pc is not None:
            if pib_pc < 3000:
                score -= 30
                penalizaciones['pib_pc'] = -30
            elif pib_pc < 6000:
                score -= 15
                penalizaciones['pib_pc'] = -15
            elif pib_pc < 12000:
                score -= 5
                penalizaciones['pib_pc'] = -5

        # Evaluación de Inflación (% anual)
        inflacion = cls._obtener_ultimo_indicador(pais, 'INFLACION')
        if inflacion is not None:
            if inflacion > 50:
                score -= 40
                penalizaciones['inflacion'] = -40
            elif inflacion > 10:
                score -= 25
                penalizaciones['inflacion'] = -25
            elif inflacion > 5:
                score -= 10
                penalizaciones['inflacion'] = -10

        # Evaluación de Desempleo (% total)
        desempleo = cls._obtener_ultimo_indicador(pais, 'DESEMPLEO')
        if desempleo is not None:
            if desempleo > 15:
                score -= 25
                penalizaciones['desempleo'] = -25
            elif desempleo > 10:
                score -= 15
                penalizaciones['desempleo'] = -15
            elif desempleo > 7:
                score -= 5
                penalizaciones['desempleo'] = -5

        # Evaluación de Deuda Gobierno (% PIB)
        deuda = cls._obtener_ultimo_indicador(pais, 'DEUDA_PIB')
        if deuda is not None:
            if deuda > 80:
                score -= 20
                penalizaciones['deuda_pib'] = -20
            elif deuda > 50:
                score -= 10
                penalizaciones['deuda_pib'] = -10

        score_final = max(0.0, float(score))
        return score_final, {'score_base': 100, 'penalizaciones': penalizaciones, 'score_calculado': score_final}

    @classmethod
    def _calcular_score_cambiario(cls, pais):
        """
        Calcula el Score Cambiario (0-100) analizando la volatilidad y depreciación de los últimos 30 días.
        """
        score = 100
        penalizaciones = {}
        
        # Recuperación del histórico de tasas de cambio de los últimos 30 días
        hace_30_dias = datetime.now().date() - timedelta(days=30)
        cambios = TipoCambio.objects.filter(moneda_origen=pais.moneda_codigo, fecha__gte=hace_30_dias).order_by('fecha')
        
        variaciones = [c.variacion_porcentual for c in cambios if c.variacion_porcentual is not None]

        if variaciones:
            # Análisis de volatilidad (Desviación estándar de las variaciones diarias)
            volatilidad = statistics.stdev(variaciones) if len(variaciones) > 1 else 0.0
            if volatilidad > 3.0:
                score -= 40
                penalizaciones['volatilidad'] = -40
            elif volatilidad > 1.5:
                score -= 25
                penalizaciones['volatilidad'] = -25
            elif volatilidad > 0.5:
                score -= 10
                penalizaciones['volatilidad'] = -10

            # Análisis de tendencia (Depreciación acumulada en el periodo)
            depreciacion = sum(variaciones)
            if depreciacion > 10:
                score -= 30
                penalizaciones['depreciacion'] = -30
            elif depreciacion > 5:
                score -= 15
                penalizaciones['depreciacion'] = -15
            elif depreciacion > 2:
                score -= 5
                penalizaciones['depreciacion'] = -5

        score_final = max(0.0, float(score))
        return score_final, {'score_base': 100, 'penalizaciones': penalizaciones, 'score_calculado': score_final}

    @classmethod
    def _calcular_score_estabilidad(cls, pais):
        """
        Calcula el Score de Estabilidad (0-100) evaluando balanza comercial, tendencia de crecimiento PIB y acumulación de riesgos.
        """
        score = 100
        penalizaciones = {}

        # Evaluación de Balanza Comercial (% PIB)
        balanza = cls._obtener_ultimo_indicador(pais, 'BALANZA_COMERCIAL')
        if balanza is not None:
            if balanza < -10:
                score -= 25
                penalizaciones['balanza_comercial'] = -25
            elif balanza < -5:
                score -= 15
                penalizaciones['balanza_comercial'] = -15
            elif balanza < 0:
                score -= 5
                penalizaciones['balanza_comercial'] = -5

        # Evaluación de Tendencia del PIB (Comparación año actual vs año anterior)
        anio_actual = datetime.now().year - 1
        pib_actual = cls._obtener_indicador_por_anio(pais, 'PIB', anio_actual)
        pib_anterior = cls._obtener_indicador_por_anio(pais, 'PIB', anio_actual - 1)

        if pib_actual and pib_anterior and pib_anterior > 0:
            crecimiento = ((pib_actual - pib_anterior) / pib_anterior) * 100
            if crecimiento < -2:
                score -= 30
                penalizaciones['crecimiento_pib'] = -30
            elif crecimiento < 0:
                score -= 20
                penalizaciones['crecimiento_pib'] = -20
            elif crecimiento < 1:
                score -= 10
                penalizaciones['crecimiento_pib'] = -10

        # Penalización por concentración de indicadores negativos
        indicadores_negativos = 0
        for tipo_ind in ['INFLACION', 'DESEMPLEO', 'DEUDA_PIB']:
            val = cls._obtener_ultimo_indicador(pais, tipo_ind)
            if val is not None:
                if tipo_ind == 'INFLACION' and val > 10: indicadores_negativos += 1
                if tipo_ind == 'DESEMPLEO' and val > 10: indicadores_negativos += 1
                if tipo_ind == 'DEUDA_PIB' and val > 50: indicadores_negativos += 1

        if indicadores_negativos > 0:
            penalizacion_ind = indicadores_negativos * 5
            score -= penalizacion_ind
            penalizaciones['indicadores_negativos'] = -penalizacion_ind

        score_final = max(0.0, float(score))
        return score_final, {'score_base': 100, 'penalizaciones': penalizaciones, 'score_calculado': score_final}

    @classmethod
    def _evaluar_alertas(cls, pais, nuevo_indice, irpc_anterior, detalle_eco):
        """
        Dispara y almacena alertas automáticas basadas en el resultado del IRPC y umbrales críticos.
        """
        # Regla 1: CRITICAL si el IRPC cae por debajo de 25
        if nuevo_indice.indice_compuesto < 25:
            Alerta.objects.create(
                pais=pais,
                tipo_alerta='RIESGO',
                severidad='CRITICAL',
                titulo=f"Riesgo Crítico en {pais.nombre}",
                mensaje=f"El índice IRPC ha descendido a {nuevo_indice.indice_compuesto}, alcanzando nivel crítico."
            )

        # Regla 2: WARNING si el IRPC cae más de 15 puntos respecto al cálculo previo
        if irpc_anterior is not None:
            caida = irpc_anterior - nuevo_indice.indice_compuesto
            if caida > 15:
                Alerta.objects.create(
                    pais=pais,
                    tipo_alerta='RIESGO',
                    severidad='WARNING',
                    titulo=f"Caída Abrupta de Riesgo ({pais.codigo_iso})",
                    mensaje=f"El IRPC cayó {round(caida, 2)} puntos respecto al período anterior (de {irpc_anterior} a {nuevo_indice.indice_compuesto})."
                )

        # Regla 3: CRITICAL por Hiperinflación si supera el 50%
        val_inf = cls._obtener_ultimo_indicador(pais, 'INFLACION')
        if val_inf is not None and val_inf > 50:
            Alerta.objects.create(
                pais=pais,
                tipo_alerta='INDICADOR',
                severidad='CRITICAL',
                titulo=f"Alerta de Hiperinflación en {pais.nombre}",
                mensaje=f"La inflación registrada es de {val_inf}%, superando el umbral crítico del 50%."
            )