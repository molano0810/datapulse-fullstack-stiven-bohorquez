from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PaisViewSet, PortafolioViewSet, IndiceRiesgoViewSet, AlertaViewSet
)

# Router principal de DRF para generar las rutas REST automáticamente
router = DefaultRouter()
router.register(r'paises', PaisViewSet, basename='pais')
router.register(r'portafolios', PortafolioViewSet, basename='portafolio')
router.register(r'riesgo', IndiceRiesgoViewSet, basename='riesgo')
router.register(r'alertas', AlertaViewSet, basename='alerta')

urlpatterns = [
    path('', include(router.urls)),
]