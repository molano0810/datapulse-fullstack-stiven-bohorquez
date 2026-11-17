from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Usuario(AbstractUser):
    """
    Extiende AbstractUser de Django para usar el email como identificador único 
    de login e incorpora el sistema de roles requerido por la prueba.
    """
    username = None  # Se elimina el username tradicional; el login opera por email.
    email = models.EmailField(unique=True, error_messages={'unique': "Ya existe un usuario con este correo."})
    nombre_completo = models.CharField(max_length=255)
    
    ROL_CHOICES = (
        ('ADMIN', 'Admin'),
        ('ANALISTA', 'Analista'),
        ('VIEWER', 'Viewer'),
    )
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default='ANALISTA')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre_completo']

    def __str__(self):
        return f"{self.email} ({self.rol})"


class Pais(models.Model):
    """
    Entidad base geográfica y monetaria para los 10 países latinoamericanos 
    monitoreados por DataPulse.
    """
    codigo_iso = models.CharField(max_length=5, primary_key=True, help_text="Ej: CO, BR, MX")
    nombre = models.CharField(max_length=100)
    moneda_codigo = models.CharField(max_length=10, help_text="Ej: COP, BRL, USD")
    moneda_nombre = models.CharField(max_length=100)
    
    REGION_CHOICES = (
        ('ANDINA', 'Andina'),
        ('CONO_SUR', 'Cono Sur'),
        ('CENTROAMERICA', 'Centroamérica'),
        ('CARIBE', 'Caribe'),
    )
    region = models.CharField(max_length=30, choices=REGION_CHOICES)
    latitud = models.FloatField()
    longitud = models.FloatField()
    poblacion = models.BigIntegerField()
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} ({self.codigo_iso})"


class IndicadorEconomico(models.Model):
    """
    Almacena variables macroeconómicas (PIB, inflación, desempleo, etc.) 
    sincronizadas desde el Banco Mundial o ingresadas de forma manual.
    """
    pais = models.ForeignKey(Pais, on_delete=models.CASCADE, related_name='indicadores')
    
    TIPO_CHOICES = (
        ('PIB', 'PIB'),
        ('INFLACION', 'Inflación'),
        ('DESEMPLEO', 'Desempleo'),
        ('BALANZA_COMERCIAL', 'Balanza Comercial'),
        ('DEUDA_PIB', 'Deuda PIB'),
        ('PIB_PERCAPITA', 'PIB Per Cápita'),
    )
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES)
    valor = models.FloatField()
    
    UNIDAD_CHOICES = (
        ('PORCENTAJE', 'Porcentaje'),
        ('USD', 'USD'),
        ('USD_MILES_MILLONES', 'USD Miles de Millones'),
    )
    unidad = models.CharField(max_length=30, choices=UNIDAD_CHOICES)
    anio = models.IntegerField()
    
    FUENTE_CHOICES = (
        ('WORLD_BANK', 'World Bank'),
        ('MANUAL', 'Manual'),
    )
    fuente = models.CharField(max_length=30, choices=FUENTE_CHOICES, default='WORLD_BANK')
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        # Restricción de negocio: Evita duplicidad de un mismo indicador para el mismo país y año.
        constraints = [
            models.UniqueConstraint(fields=['pais', 'tipo', 'anio'], name='unique_indicador_pais_anio')
        ]

    def __str__(self):
        return f"{self.pais.codigo_iso} - {self.tipo} ({self.anio}): {self.valor}"


class TipoCambio(models.Model):
    """
    Registra el histórico diario de las tasas de cambio de las monedas locales frente al USD 
    junto con su variación porcentual.
    """
    moneda_origen = models.CharField(max_length=10) # Enlace lógico con Pais.moneda_codigo
    moneda_destino = models.CharField(max_length=10, default="USD")
    tasa = models.FloatField()
    fecha = models.DateField()
    variacion_porcentual = models.FloatField(default=0.0, help_text="Variación respecto al día anterior[cite: 3]")
    fuente = models.CharField(max_length=50, default="ExchangeRate-API")

    def __str__(self):
        return f"{self.moneda_origen}/{self.moneda_destino} - {self.fecha}: {self.tasa}"


class Portafolio(models.Model):
    """
    Portafolios de inversión simulados creados por los analistas, 
    pudiendo ser públicos o privados.
    """
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='portafolios')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)
    es_publico = models.BooleanField(default=False, help_text="Visible para otros usuarios[cite: 3]")

    class Meta:
        # Restricción. Un mismo usuario no puede repetir nombres de portafolios.
        constraints = [
            models.UniqueConstraint(fields=['usuario', 'nombre'], name='unique_portafolio_usuario_nombre')
        ]

    def __str__(self):
        return f"{self.nombre} por {self.usuario.email}"


class Posicion(models.Model):
    """
    Representa activos individuales dentro de un portafolio de inversión 
    (renta fija, variable, commodities o monedas).
    """
    portafolio = models.ForeignKey(Portafolio, on_delete=models.CASCADE, related_name='posiciones')
    pais = models.ForeignKey(Pais, on_delete=models.CASCADE, related_name='posiciones')
    
    TIPO_ACTIVO_CHOICES = (
        ('RENTA_FIJA', 'Renta Fija'),
        ('RENTA_VARIABLE', 'Renta Variable'),
        ('COMMODITIES', 'Commodities'),
        ('MONEDA', 'Moneda'),
    )
    tipo_activo = models.CharField(max_length=30, choices=TIPO_ACTIVO_CHOICES)
    monto_inversion_usd = models.FloatField(validators=[MinValueValidator(1.0)])
    fecha_entrada = models.DateField()
    fecha_salida = models.DateField(blank=True, null=True, help_text="Nullable para posiciones activas[cite: 3]")
    notas = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.portafolio.nombre} -> {self.pais.codigo_iso} ({self.tipo_activo}): ${self.monto_inversion_usd}"


class IndiceRiesgo(models.Model):
    """
    Almacena el Índice de Riesgo País Compuesto (IRPC) calculado automáticamente 
    combinando scores económicos, cambiarios y de estabilidad.
    """
    pais = models.ForeignKey(Pais, on_delete=models.CASCADE, related_name='indices_riesgo')
    fecha_calculo = models.DateTimeField(auto_now_add=True)
    score_economico = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    score_cambiario = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    score_estabilidad = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Restricción de integridad: El índice compuesto siempre debe mantenerse entre 0 y 100.
    indice_compuesto = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    NIVEL_RIESGO_CHOICES = (
        ('BAJO', 'Bajo'),
        ('MODERADO', 'Moderado'),
        ('ALTO', 'Alto'),
        ('CRITICO', 'Crítico'),
    )
    nivel_riesgo = models.CharField(max_length=20, choices=NIVEL_RIESGO_CHOICES)
    detalle_calculo = models.JSONField(help_text="JSONField que almacena el desglose detallado del algoritmo[cite: 3]")

    def __str__(self):
        return f"IRPC {self.pais.codigo_iso}: {self.indice_compuesto} ({self.nivel_riesgo})"


class Alerta(models.Model):
    """
    Sistema de notificaciones automáticas ante variaciones drásticas de riesgo, 
    tipos de cambio o eventos de sincronización.
    """
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='alertas', blank=True, null=True, help_text="Nullable para alertas globales[cite: 3]")
    pais = models.ForeignKey(Pais, on_delete=models.CASCADE, related_name='alertas', blank=True, null=True)
    
    TIPO_ALERTA_CHOICES = (
        ('RIESGO', 'Riesgo'),
        ('TIPO_CAMBIO', 'Tipo de Cambio'),
        ('INDICADOR', 'Indicador'),
    )
    tipo_alerta = models.CharField(max_length=30, choices=TIPO_ALERTA_CHOICES)
    
    SEVERIDAD_CHOICES = (
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('CRITICAL', 'Critical'),
    )
    severidad = models.CharField(max_length=20, choices=SEVERIDAD_CHOICES)
    titulo = models.CharField(max_length=255)
    mensaje = models.TextField()
    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.severidad}] {self.titulo}"


class LogActividad(models.Model):
    """
    Registro de auditoría (logs) para rastrear acciones CRUD, inicios de sesión 
    y exportaciones realizadas en la plataforma.
    """
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, related_name='logs')
    
    ACCION_CHOICES = (
        ('CREAR', 'Crear'),
        ('EDITAR', 'Editar'),
        ('ELIMINAR', 'Eliminar'),
        ('CONSULTAR', 'Consultar'),
        ('LOGIN', 'Login'),
        ('EXPORT', 'Export'),
    )
    accion = models.CharField(max_length=20, choices=ACCION_CHOICES)
    entidad_afectada = models.CharField(max_length=100, help_text="Nombre del modelo afectado")
    entidad_id = models.IntegerField(blank=True, null=True)
    detalle = models.JSONField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario} - {self.accion} {self.entidad_afectada} ({self.fecha})"