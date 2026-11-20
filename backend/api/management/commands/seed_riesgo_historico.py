import random
from datetime import timedelta

from django.core.management.base import BaseCommand

from api.models import Pais, IndiceRiesgo


def clasificar(indice):
    if indice >= 75:
        return 'BAJO'
    if indice >= 50:
        return 'MODERADO'
    if indice >= 25:
        return 'ALTO'
    return 'CRITICO'


def limitar(valor):
    return max(0.0, min(100.0, round(valor, 1)))


class Command(BaseCommand):
    help = (
        'Genera 6 semanas de histórico SIMULADO de IRPC hacia atrás desde el '
        'último cálculo real, para poblar ranking (variación/tendencia) y gráficos.'
    )
    SEMANAS = 6

    def handle(self, *args, **kwargs):
        rng = random.Random(2026)  # semilla fija: resultado reproducible

        for pais in Pais.objects.filter(activo=True):
            # Idempotencia: elimina solo lo simulado en ejecuciones anteriores
            IndiceRiesgo.objects.filter(pais=pais, detalle_calculo__simulado=True).delete()

            actual = IndiceRiesgo.objects.filter(pais=pais).order_by('-fecha_calculo').first()
            if not actual:
                self.stdout.write(self.style.WARNING(f'{pais.codigo_iso}: sin IRPC real, ejecuta run_sync primero'))
                continue

            fecha_base = actual.fecha_calculo
            eco, camb, est = actual.score_economico, actual.score_cambiario, actual.score_estabilidad

            for k in range(1, self.SEMANAS + 1):
                eco = limitar(eco + rng.uniform(-2, 2))
                camb = limitar(camb + rng.uniform(-3, 3))
                est = limitar(est + rng.uniform(-1.5, 1.5))
                compuesto = round(eco * 0.40 + camb * 0.30 + est * 0.30, 2)

                registro = IndiceRiesgo.objects.create(
                    pais=pais,
                    score_economico=eco,
                    score_cambiario=camb,
                    score_estabilidad=est,
                    indice_compuesto=compuesto,
                    nivel_riesgo=clasificar(compuesto),
                    detalle_calculo={'simulado': True, 'nota': 'Histórico simulado para datos de prueba'},
                )
                # fecha_calculo es auto_now_add: se ajusta con update()
                IndiceRiesgo.objects.filter(pk=registro.pk).update(fecha_calculo=fecha_base - timedelta(weeks=k))

            # Se recrea el registro real para que conserve el id más alto
            datos = dict(
                pais=pais,
                score_economico=actual.score_economico,
                score_cambiario=actual.score_cambiario,
                score_estabilidad=actual.score_estabilidad,
                indice_compuesto=actual.indice_compuesto,
                nivel_riesgo=actual.nivel_riesgo,
                detalle_calculo=actual.detalle_calculo,
            )
            actual.delete()
            nuevo = IndiceRiesgo.objects.create(**datos)
            IndiceRiesgo.objects.filter(pk=nuevo.pk).update(fecha_calculo=fecha_base)

            self.stdout.write(self.style.SUCCESS(f'{pais.codigo_iso}: histórico de {self.SEMANAS} semanas listo'))
