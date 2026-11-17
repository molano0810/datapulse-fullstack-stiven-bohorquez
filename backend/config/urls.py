from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Endpoints de la API REST de DataPulse
    path('api/', include('api.urls')),
    
    # Endpoints de Autenticación JWT (Login, Refresh) requeridos por la prueba[cite: 4, 9]
    path('api/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]