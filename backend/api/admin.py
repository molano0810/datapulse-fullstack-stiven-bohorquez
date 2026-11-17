from django.contrib import admin
from .models import Usuario, Pais, IndicadorEconomico, TipoCambio, Portafolio, Posicion, IndiceRiesgo, Alerta, LogActividad

# Registramos todos los modelos para gestionarlos desde /admin/
admin.site.register(Usuario)
admin.site.register(Pais)
admin.site.register(IndicadorEconomico)
admin.site.register(TipoCambio)
admin.site.register(Portafolio)
admin.site.register(Posicion)
admin.site.register(IndiceRiesgo)
admin.site.register(Alerta)
admin.site.register(LogActividad)