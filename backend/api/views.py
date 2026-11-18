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
from .services_irpc import IRPCService

from rest_framework import generics
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer

class CustomTokenObtainPairView(TokenObtainPairView):
    """POST /api/auth/login/ - Autentica al usuario y retorna access + refresh tokens."""
    serializer_class = CustomTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    """POST /api/auth/register/ - Registro de nuevos usuarios."""
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [permissions.AllowAny]


class PerfilUsuarioView(APIView):
    """GET /api/auth/me/ - Retorna los datos del usuario autenticado mediante el Bearer Token."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UsuarioSerializer(request.user)
        return Response(serializer.data)


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
    API endpoint para consultar el ranking, detalle, histórico y recálculo 
    del Índice de Riesgo País Compuesto (IRPC).
    """
    serializer_class = IndiceRiesgoSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['pais', 'nivel_riesgo']
    ordering_fields = ['indice_compuesto', 'fecha_calculo']
    ordering = ['-indice_compuesto']  # Por defecto ordena de menor riesgo (mayor puntaje) a mayor riesgo

    def get_queryset(self):
        """
        Para el listado general (/api/riesgo/), retorna únicamente el cálculo más reciente 
        de cada país para conformar el ranking vigente.
        """
        if self.action == 'list':
            # Subconsulta para obtener el ID del último registro calculado por cada país
            ultimos_ids = (
                IndiceRiesgo.objects.values('pais')
                .annotate(ultimo_id=models.Max('id'))
                .values_list('ultimo_id', flat=True)
            )
            return IndiceRiesgo.objects.filter(id__in=ultimos_ids).select_related('pais')
        
        return IndiceRiesgo.objects.all().select_related('pais').order_by('-fecha_calculo')

    def retrieve(self, request, pk=None):
        """
        GET /api/riesgo/{codigo_iso}/
        Retorna el detalle de riesgo actual de un país junto con su histórico reciente[cite: 6].
        """
        ultimo_indice = IndiceRiesgo.objects.filter(pais__codigo_iso__iexact=pk).order_by('-fecha_calculo').first()
        if not ultimo_indice:
            return Response(
                {"error": f"No se encontraron registros de riesgo para el país '{pk}'."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        historico = IndiceRiesgo.objects.filter(pais__codigo_iso__iexact=pk).order_by('-fecha_calculo')[:30]
        
        data = self.get_serializer(ultimo_indice).data
        data['historico'] = self.get_serializer(historico, many=True).data
        return Response(data)

    @action(detail=True, methods=['get'], url_path='historico')
    def historico(self, request, pk=None):
        """
        GET /api/riesgo/{codigo_iso}/historico/
        Retorna el histórico de índices de un país con filtro opcional por rango de fechas[cite: 6].
        """
        qs = IndiceRiesgo.objects.filter(pais__codigo_iso__iexact=pk).order_by('-fecha_calculo')
        
        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin = request.query_params.get('fecha_fin')
        if fecha_inicio and fecha_fin:
            qs = qs.filter(fecha_calculo__date__range=[fecha_inicio, fecha_fin])
            
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='calcular')
    def calcular(self, request):
        """
        POST /api/riesgo/calcular/
        Dispara el recálculo global del IRPC para todos los países (exclusivo rol ADMIN)[cite: 6].
        """
        if getattr(request.user, 'rol', '') != 'ADMIN' and not request.user.is_staff:
            return Response(
                {"error": "No tiene permisos suficientes. Solo un administrador puede recalcular el IRPC."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        exito, mensaje = IRPCService.calcular_todos_los_paises(usuario=request.user)
        if exito:
            return Response({"mensaje": mensaje}, status=status.HTTP_200_OK)
        return Response({"error": mensaje}, status=status.HTTP_400_BAD_REQUEST)


class AlertaViewSet(viewsets.ModelViewSet):
    """
    API endpoint para consultar, filtrar, marcar como leídas y resumir alertas del usuario[cite: 6].
    """
    serializer_class = AlertaSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['leida', 'tipo_alerta', 'severidad']
    ordering = ['-fecha_creacion']

    def get_queryset(self):
        """Retorna alertas dirigidas al usuario autenticado o alertas globales del sistema[cite: 4]."""
        user = self.request.user
        return Alerta.objects.filter(
            models.Q(usuario=user) | models.Q(usuario__isnull=True)
        ).select_related('pais').order_by('-fecha_creacion')

    @action(detail=True, methods=['put'], url_path='leer')
    def marcar_como_leida(self, request, pk=None):
        """PUT /api/alertas/{id}/leer/ - Marca una alerta individual como leída[cite: 6]."""
        alerta = self.get_object()
        alerta.leida = True
        alerta.save()
        return Response({"status": "Alerta marcada como leída"})

    @action(detail=False, methods=['put'], url_path='leer-todas')
    def marcar_todas_como_leidas(self, request):
        """PUT /api/alertas/leer-todas/ - Marca todas las alertas pendientes del usuario como leídas[cite: 6]."""
        self.get_queryset().filter(leida=False).update(leida=True)
        return Response({"status": "Todas las alertas marcadas como leídas"})

    @action(detail=False, methods=['get'], url_path='resumen')
    def resumen(self, request):
        """
        GET /api/alertas/resumen/
        Retorna el conteo de alertas agrupadas por tipo y severidad[cite: 6].
        """
        qs = self.get_queryset()
        no_leidas = qs.filter(leida=False)
        
        return Response({
            "total": qs.count(),
            "no_leidas": no_leidas.count(),
            "por_severidad": {
                "CRITICAL": no_leidas.filter(severidad='CRITICAL').count(),
                "WARNING": no_leidas.filter(severidad='WARNING').count(),
                "INFO": no_leidas.filter(severidad='INFO').count(),
            },
            "por_tipo": {
                "RIESGO": no_leidas.filter(tipo_alerta='RIESGO').count(),
                "TIPO_CAMBIO": no_leidas.filter(tipo_alerta='TIPO_CAMBIO').count(),
                "INDICADOR": no_leidas.filter(tipo_alerta='INDICADOR').count(),
            }
        })