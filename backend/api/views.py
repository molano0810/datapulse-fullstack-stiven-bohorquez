from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db import models

from .models import Usuario, Pais, IndicadorEconomico, TipoCambio, Portafolio, Posicion, IndiceRiesgo, Alerta, LogActividad
from .serializers import (
    UsuarioSerializer, PaisSerializer, IndicadorEconomicoSerializer,
    TipoCambioSerializer, PortafolioSerializer, PosicionSerializer,
    IndiceRiesgoSerializer, AlertaSerializer, LogActividadSerializer
)


class EsAdminOReadOnly(permissions.BasePermission):
    """
    Permiso personalizado: Solo los administradores pueden modificar (POST/PUT/DELETE),
    mientras que los analistas y viewers tienen acceso de solo lectura (GET).
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return request.user and request.user.is_authenticated and request.user.rol == 'ADMIN'


class SoloAnalistaOAdmin(permissions.BasePermission):
    """
    Permiso personalizado: Un VIEWER no puede crear ni editar portafolios[cite: 4].
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        # Viewer tiene prohibido crear/modificar
        return request.user.rol in ['ADMIN', 'ANALISTA']


class PaisViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint para listar y consultar detalles de países e indicadores económicos[cite: 4].
    """
    queryset = Pais.objects.all()
    serializer_class = PaisSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['region', 'activo']
    search_fields = ['nombre', 'codigo_iso', 'moneda_codigo']
    ordering_fields = ['nombre', 'poblacion']

    @action(detail=True, methods=['get'])
    def indicadores(self, request, pk=None):
        """Retorna los indicadores económicos de un país con filtros opcionales por tipo y año[cite: 4]."""
        pais = self.get_object()
        indicadores = pais.indicadores.all()
        
        tipo = request.query_params.get('tipo')
        anio = request.query_params.get('anio')
        if tipo:
            indicadores = indicadores.filter(tipo=tipo)
        if anio:
            indicadores = indicadores.filter(anio=anio)
            
        serializer = IndicadorEconomicoSerializer(indicadores, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='tipo-cambio')
    def tipo_cambio(self, request, pk=None):
        """Retorna el histórico de tipo de cambio de la moneda del país[cite: 4]."""
        pais = self.get_object()
        historico = TipoCambio.objects.filter(moneda_origen=pais.moneda_codigo)
        
        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin = request.query_params.get('fecha_fin')
        if fecha_inicio and fecha_fin:
            historico = historico.filter(fecha__range=[fecha_inicio, fecha_fin])
            
        serializer = TipoCambioSerializer(historico, many=True)
        return Response(serializer.data)


class PortafolioViewSet(viewsets.ModelViewSet):
    """
    API endpoint para la gestión completa de portafolios de inversión y sus posiciones[cite: 5].
    """
    serializer_class = PortafolioSerializer
    permission_classes = [permissions.IsAuthenticated, SoloAnalistaOAdmin]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['nombre', 'descripcion']
    ordering_fields = ['fecha_creacion', 'nombre']

    def get_queryset(self):
        """Un usuario ve sus propios portafolios y los que son públicos[cite: 5]."""
        user = self.request.user
        if user.is_staff or user.rol == 'ADMIN':
            return Portafolio.objects.all()
        return Portafolio.objects.filter(models.Q(usuario=user) | models.Q(es_publico=True), activo=True)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

    @action(detail=True, methods=['post'], url_path='posiciones')
    def agregar_posicion(self, request, pk=None):
        """Agrega una posición al portafolio validando reglas de negocio[cite: 5]."""
        portafolio = self.get_object()
        data = request.data.copy()
        data['portafolio'] = portafolio.id
        
        serializer = PosicionSerializer(data=data)
        if serializer.is_valid():
            # Validación de regla de negocio: Monto total del portafolio no puede superar $50,000,000 USD[cite: 11]
            monto_nuevo = serializer.validated_data['monto_inversion_usd']
            monto_actual = sum(p.monto_inversion_usd for p in portafolio.posiciones.filter(fecha_salida__isnull=True))
            if monto_actual + monto_nuevo > 50000000:
                return Response(
                    {"error": "El monto total del portafolio superaría el límite permitido de $50,000,000 USD."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class IndiceRiesgoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint para consultar el ranking y detalle del Índice de Riesgo País Compuesto (IRPC)[cite: 5].
    """
    queryset = IndiceRiesgo.objects.all()
    serializer_class = IndiceRiesgoSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['pais', 'nivel_riesgo']
    ordering_fields = ['indice_compuesto', 'fecha_calculo']

class AlertaViewSet(viewsets.ModelViewSet):
    """
    API endpoint para consultar y gestionar las alertas del usuario[cite: 5].
    """
    serializer_class = AlertaSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['leida', 'tipo_alerta', 'severidad']

    def get_queryset(self):
        user = self.request.user
        return Alerta.objects.filter(models.Q(usuario=user) | models.Q(usuario__isnull=True))

    @action(detail=True, methods=['put'], url_path='leer')
    def marcar_como_leida(self, request, pk=None):
        alerta = self.get_object()
        alerta.leida = True
        alerta.save()
        return Response({"status": "Alerta marcada como leída"})

    @action(detail=False, methods=['put'], url_path='leer-todas')
    def marcar_todas_como_leidas(self, request):
        self.get_queryset().update(leida=True)
        return Response({"status": "Todas las alertas marcadas como leídas"})