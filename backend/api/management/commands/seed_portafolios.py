from datetime import date

from django.core.management.base import BaseCommand

from api.models import Portafolio, Posicion, Usuario


PORTAFOLIOS = [
    {
        'email': 'analista@datapulse.com',
        'nombre': 'Portafolio Latam Crecimiento',
        'descripcion': 'Inversión diversificada en mercados emergentes de Latinoamérica con foco en crecimiento.',
        'es_publico': True,
        'posiciones': [
            ('CO', 'RENTA_VARIABLE', 250000, date(2026, 3, 10), None, 'Energía e infraestructura'),
            ('BR', 'RENTA_FIJA', 400000, date(2026, 2, 5), None, 'Bonos soberanos'),
            ('MX', 'COMMODITIES', 150000, date(2026, 4, 20), None, 'Exposición a petróleo'),
            ('CL', 'RENTA_FIJA', 300000, date(2026, 1, 15), None, 'Bonos corporativos'),
            ('PE', 'MONEDA', 100000, date(2026, 5, 2), None, 'Cobertura cambiaria'),
        ],
    },
    {
        'email': 'admin@datapulse.com',
        'nombre': 'Fondo Infraestructura Andina',
        'descripcion': 'Fondo privado enfocado en la región andina y economías dolarizadas.',
        'es_publico': False,
        'posiciones': [
            ('CO', 'RENTA_FIJA', 500000, date(2026, 2, 12), None, 'TES de largo plazo'),
            ('PE', 'RENTA_VARIABLE', 200000, date(2026, 3, 18), None, 'Minería'),
            ('EC', 'RENTA_FIJA', 150000, date(2026, 6, 1), None, 'Deuda dolarizada'),
            ('UY', 'MONEDA', 80000, date(2026, 7, 7), None, 'Posición cambiaria'),
            ('AR', 'RENTA_VARIABLE', 60000, date(2026, 1, 15), date(2026, 9, 30), 'Posición cerrada'),
        ],
    },
]


class Command(BaseCommand):
    help = 'Crea 2 portafolios de ejemplo con posiciones (datos de prueba, idempotente).'

    def handle(self, *args, **kwargs):
        for datos in PORTAFOLIOS:
            usuario = Usuario.objects.get(email=datos['email'])
            portafolio, creado = Portafolio.objects.get_or_create(
                usuario=usuario,
                nombre=datos['nombre'],
                defaults={'descripcion': datos['descripcion'], 'es_publico': datos['es_publico']},
            )
            if portafolio.posiciones.exists():
                self.stdout.write(f'{portafolio.nombre}: ya tiene posiciones, se omite')
                continue

            for pais, tipo, monto, entrada, salida, notas in datos['posiciones']:
                Posicion.objects.create(
                    portafolio=portafolio,
                    pais_id=pais,
                    tipo_activo=tipo,
                    monto_inversion_usd=monto,
                    fecha_entrada=entrada,
                    fecha_salida=salida,
                    notas=notas,
                )
            self.stdout.write(self.style.SUCCESS(
                f'{portafolio.nombre}: {len(datos["posiciones"])} posiciones ({"creado" if creado else "existente"})'
            ))
