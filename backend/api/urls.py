from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    PaisViewSet, PortafolioViewSet, IndiceRiesgoViewSet, AlertaViewSet,
    LogActividadViewSet, DashboardResumenView,
    CustomTokenObtainPairView, RegisterView, PerfilUsuarioView
)

router = DefaultRouter()
router.register(r'paises', PaisViewSet, basename='pais')
router.register(r'portafolios', PortafolioViewSet, basename='portafolio')
router.register(r'riesgo', IndiceRiesgoViewSet, basename='riesgo')
router.register(r'alertas', AlertaViewSet, basename='alerta')
router.register(r'logs', LogActividadViewSet, basename='log')

urlpatterns = [
    path('', include(router.urls)),
    # Dashboard ejecutivo
    path('dashboard/resumen/', DashboardResumenView.as_view(), name='dashboard_resumen'),
    # Autenticación JWT
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/register/', RegisterView.as_view(), name='auth_register'),
    path('auth/me/', PerfilUsuarioView.as_view(), name='auth_me'),
]