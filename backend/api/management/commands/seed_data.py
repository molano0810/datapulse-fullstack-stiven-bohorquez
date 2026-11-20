from django.core.management.base import BaseCommand
from api.models import Usuario, Pais


class Command(BaseCommand):
    help = 'Pobla la base de datos con los 10 países de LATAM y los usuarios de prueba obligatorios de DataPulse.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Iniciando carga de datos iniciales (Seed)...'))

        # 1. Crear Usuarios Obligatorios de la Prueba
        usuarios_data = [
            {
                'email': 'admin@datapulse.com',
                'nombre_completo': 'Administrador DataPulse',
                'password': 'DataPulse2026!',
                'rol': 'ADMIN',
                'is_staff': True,
                'is_superuser': True,
            },
            {
                'email': 'analista@datapulse.com',
                'nombre_completo': 'Analista Financiero',
                'password': 'DataPulse2026!',
                'rol': 'ANALISTA',
                'is_staff': False,
                'is_superuser': False,
            },
            {
                'email': 'viewer@datapulse.com',
                'nombre_completo': 'Visualizador DataPulse',
                'password': 'DataPulse2026!',
                'rol': 'VIEWER',
                'is_staff': False,
                'is_superuser': False,
            },
        ]

        for u_data in usuarios_data:
            email = u_data['email']
            password = u_data.pop('password')
            
            usuario, created = Usuario.objects.update_or_create(
                email=email,
                defaults=u_data
            )
            if created or not usuario.check_password(password):
                usuario.set_password(password)
                usuario.save()
                self.stdout.write(self.style.SUCCESS(f'Usuario creado/actualizado: {email} ({u_data["rol"]})'))

        # 2. Crear los 10 Países Latinoamericanos
        paises_data = [
            {'codigo_iso': 'CO', 'nombre': 'Colombia', 'moneda_codigo': 'COP', 'moneda_nombre': 'Peso Colombiano', 'region': 'ANDINA', 'latitud': 4.5709, 'longitud': -74.2973, 'poblacion': 51516000},
            {'codigo_iso': 'BR', 'nombre': 'Brasil', 'moneda_codigo': 'BRL', 'moneda_nombre': 'Real Brasileño', 'region': 'CONO_SUR', 'latitud': -14.2350, 'longitud': -51.9253, 'poblacion': 214300000},
            {'codigo_iso': 'MX', 'nombre': 'México', 'moneda_codigo': 'MXN', 'moneda_nombre': 'Peso Mexicano', 'region': 'CENTROAMERICA', 'latitud': 23.6345, 'longitud': -102.5528, 'poblacion': 128900000},
            {'codigo_iso': 'AR', 'nombre': 'Argentina', 'moneda_codigo': 'ARS', 'moneda_nombre': 'Peso Argentino', 'region': 'CONO_SUR', 'latitud': -38.4161, 'longitud': -63.6167, 'poblacion': 45810000},
            {'codigo_iso': 'CL', 'nombre': 'Chile', 'moneda_codigo': 'CLP', 'moneda_nombre': 'Peso Chileno', 'region': 'CONO_SUR', 'latitud': -35.6751, 'longitud': -71.5430, 'poblacion': 19490000},
            {'codigo_iso': 'PE', 'nombre': 'Perú', 'moneda_codigo': 'PEN', 'moneda_nombre': 'Sol Peruano', 'region': 'ANDINA', 'latitud': -9.1900, 'longitud': -75.0152, 'poblacion': 33300000},
            {'codigo_iso': 'EC', 'nombre': 'Ecuador', 'moneda_codigo': 'USD', 'moneda_nombre': 'Dólar Estadounidense', 'region': 'ANDINA', 'latitud': -1.8312, 'longitud': -78.1834, 'poblacion': 17800000},
            {'codigo_iso': 'UY', 'nombre': 'Uruguay', 'moneda_codigo': 'UYU', 'moneda_nombre': 'Peso Uruguayo', 'region': 'CONO_SUR', 'latitud': -32.5228, 'longitud': -55.7658, 'poblacion': 3426000},
            {'codigo_iso': 'PY', 'nombre': 'Paraguay', 'moneda_codigo': 'PYG', 'moneda_nombre': 'Guaraní Paraguayo', 'region': 'CONO_SUR', 'latitud': -23.4425, 'longitud': -58.4438, 'poblacion': 6781000},
            {'codigo_iso': 'PA', 'nombre': 'Panamá', 'moneda_codigo': 'PAB', 'moneda_nombre': 'Balboa Panameño', 'region': 'CENTROAMERICA', 'latitud': 8.5379, 'longitud': -80.7821, 'poblacion': 4404000},
        ]

        for p_data in paises_data:
            codigo = p_data['codigo_iso']
            Pais.objects.update_or_create(
                codigo_iso=codigo,
                defaults=p_data
            )
            self.stdout.write(self.style.SUCCESS(f'País sincronizado: {p_data["nombre"]} ({codigo})'))

        self.stdout.write(self.style.SUCCESS('¡Seed completado exitosamente! Base de datos inicializada.'))