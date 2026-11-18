from django.core.management.base import BaseCommand
from api.services import ExternalDataSyncService
from api.services_irpc import IRPCService


class Command(BaseCommand):
    help = 'Ejecuta la sincronización de indicadores (Banco Mundial), tasas de cambio (ExchangeRate-API) y recalcula el IRPC.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Iniciando proceso de sincronización con APIs externas...'))

        # 1. Sincronizar Indicadores Macroeconómicos del Banco Mundial
        self.stdout.write('1. Consultando API del Banco Mundial...')
        success_wb, msg_wb = ExternalDataSyncService.sincronizar_indicadores_banco_mundial()
        if success_wb:
            self.stdout.write(self.style.SUCCESS(f'   [OK] {msg_wb}'))
        else:
            self.stdout.write(self.style.ERROR(f'   [ERROR] {msg_wb}'))

        # 2. Sincronizar Tasas de Cambio (ExchangeRate-API)
        self.stdout.write('2. Consultando ExchangeRate-API...')
        success_fx, msg_fx = ExternalDataSyncService.sincronizar_tasas_cambio()
        if success_fx:
            self.stdout.write(self.style.SUCCESS(f'   [OK] {msg_fx}'))
        else:
            self.stdout.write(self.style.ERROR(f'   [ERROR] {msg_fx}'))

        # 3. Recalcular Índice de Riesgo País Compuesto (IRPC) y evaluar alertas automáticas
        self.stdout.write('3. Recalculando Índice de Riesgo País Compuesto (IRPC)...')
        success_irpc, msg_irpc = IRPCService.calcular_todos_los_paises()
        if success_irpc:
            self.stdout.write(self.style.SUCCESS(f'   [OK] {msg_irpc}'))
        else:
            self.stdout.write(self.style.ERROR(f'   [ERROR] {msg_irpc}'))

        self.stdout.write(self.style.SUCCESS('¡Flujo completo de sincronización y cálculo de riesgo finalizado!'))