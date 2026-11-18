from django.core.management.base import BaseCommand
from api.services_irpc import IRPCService

class Command(BaseCommand):
    help = 'Calcula el Índice de Riesgo País Compuesto (IRPC) para todos los países activos.'

    def handle(self, *args, **options):
        self.stdout.write("Iniciando cálculo de IRPC y generación de alertas...")
        exito, mensaje = IRPCService.calcular_todos_los_paises()
        if exito:
            self.stdout.write(self.style.SUCCESS(mensaje))
        else:
            self.stdout.write(self.style.ERROR(f"Error: {mensaje}"))