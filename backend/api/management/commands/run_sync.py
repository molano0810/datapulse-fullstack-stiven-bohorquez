from django.core.management.base import BaseCommand
from api.services import ExternalDataSyncService


class Command(BaseCommand):
    help = 'Ejecuta manualmente la sincronización de indicadores macroeconómicos (Banco Mundial) y tasas de cambio (ExchangeRate-API).'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Iniciando proceso de sincronización con APIs externas...'))

        # 1. Sincronizar Indicadores Macroeconómicos del Banco Mundial
        self.stdout.write('Consultando API del Banco Mundial...')
        success_wb, msg_wb = ExternalDataSyncService.sincronizar_indicadores_banco_mundial()
        
        if success_wb:
            self.stdout.write(self.style.SUCCESS(f' [OK] {msg_wb}'))
        else:
            self.stdout.write(self.style.ERROR(f' [ERROR] {msg_wb}'))

        # 2. Sincronizar Tasas de Cambio (ExchangeRate-API)
        self.stdout.write('Consultando ExchangeRate-API...')
        success_fx, msg_fx = ExternalDataSyncService.sincronizar_tasas_cambio()
        
        if success_fx:
            self.stdout.write(self.style.SUCCESS(f' [OK] {msg_fx}'))
        else:
            self.stdout.write(self.style.ERROR(f' [ERROR] {msg_fx}'))

        self.stdout.write(self.style.SUCCESS('¡Proceso de sincronización finalizado!'))