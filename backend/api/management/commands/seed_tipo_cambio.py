import random
from datetime import timedelta

from django.core.management.base import BaseCommand

from api.models import Pais, TipoCambio


class Command(BaseCommand):
    help = (
        'Genera 30 días de histórico SIMULADO de tipo de cambio, hacia atrás '
        'desde la última tasa real sincronizada (solo datos de prueba).'
    )

    def handle(self, *args, **kwargs):
        rng = random.Random(2026)  # semilla fija: resultado reproducible

        for pais in Pais.objects.filter(activo=True):
            moneda = pais.moneda_codigo
            base = TipoCambio.objects.filter(moneda_origen=moneda).order_by('-fecha').first()
            if not base:
                self.stdout.write(self.style.WARNING(f'{moneda}: sin tasa base, ejecuta run_sync primero'))
                continue

            volatilidad = 0.0 if moneda == 'USD' else 0.6  # % diario aproximado

            # Tasas simuladas hacia atrás a partir de la tasa real más reciente
            tasas = {base.fecha: base.tasa}
            tasa = base.tasa
            for i in range(1, 30):
                tasa = tasa / (1 + rng.gauss(0, volatilidad) / 100)
                tasas[base.fecha - timedelta(days=i)] = tasa

            anterior = None
            for fecha in sorted(tasas):
                existente = TipoCambio.objects.filter(
                    moneda_origen=moneda, moneda_destino='USD', fecha=fecha
                ).first()
                valor = existente.tasa if existente else tasas[fecha]
                variacion = 0.0 if anterior is None else round((valor - anterior) / anterior * 100, 4)

                if existente:
                    existente.variacion_porcentual = variacion
                    existente.save(update_fields=['variacion_porcentual'])
                else:
                    TipoCambio.objects.create(
                        moneda_origen=moneda,
                        moneda_destino='USD',
                        fecha=fecha,
                        tasa=valor,
                        variacion_porcentual=variacion,
                        fuente='Seed (simulado)',
                    )
                anterior = valor

            self.stdout.write(self.style.SUCCESS(f'{moneda}: histórico de 30 días listo'))
