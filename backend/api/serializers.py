from rest_framework import serializers
from .models import Usuario, Pais, IndicadorEconomico, TipoCambio, Portafolio, Posicion, IndiceRiesgo, Alerta, LogActividad
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Personaliza el payload y la respuesta del login JWT incluyendo datos básicos del usuario.
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['rol'] = user.rol
        token['nombre_completo'] = user.nombre_completo
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = {
            'id': self.user.id,
            'email': self.user.email,
            'nombre_completo': self.user.nombre_completo,
            'rol': self.user.rol,
        }
        return data
class UsuarioSerializer(serializers.ModelSerializer):
    """
    Serializador para la entidad Usuario. Maneja la representación y 
    creación segura de usuarios con cifrado de contraseña.
    """
    class Meta:
        model = Usuario
        fields = ['id', 'email', 'nombre_completo', 'rol', 'fecha_creacion', 'activo', 'password']
        extra_kwargs = {'password': {'write_only': True}} # Evita que la contraseña se devuelva en las respuestas GET

    def create(self, validated_data):
        # Sobrescribimos create para asegurar que la contraseña se guarde hasheada con el sistema de Django
        password = validated_data.pop('password', None)
        user = super().create(validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


class PaisSerializer(serializers.ModelSerializer):
    """
    Serializador para la entidad País (datos geográficos, monetarios y demográficos).
    """
    class Meta:
        model = Pais
        fields = '__all__'


class IndicadorEconomicoSerializer(serializers.ModelSerializer):
    """
    Serializador para los indicadores macroeconómicos asociados a un país.
    """
    pais_nombre = serializers.ReadOnlyField(source='pais.nombre')

    class Meta:
        model = IndicadorEconomico
        fields = '__all__'


class TipoCambioSerializer(serializers.ModelSerializer):
    """
    Serializador para el histórico de tipos de cambio diarios y su variación porcentual.
    """
    class Meta:
        model = TipoCambio
        fields = '__all__'


class PosicionSerializer(serializers.ModelSerializer):
    """
    Serializador para las posiciones individuales dentro de un portafolio de inversión.
    Incluye validación para asegurar que el monto cumpla con los mínimos de negocio.
    """
    pais_nombre = serializers.ReadOnlyField(source='pais.nombre')

    class Meta:
        model = Posicion
        fields = '__all__'

    def validate_monto_inversion_usd(self, value):
        if value < 1000:
            raise serializers.ValidationError("El monto mínimo de inversión por posición es de $1,000 USD.")
        return value


class PortafolioSerializer(serializers.ModelSerializer):
    """
    Serializador avanzado para Portafolios. Incluye las posiciones relacionadas 
    anidadas para lectura y el usuario creador de forma automática.
    """
    posiciones = PosicionSerializer(many=True, read_only=True)
    usuario_email = serializers.ReadOnlyField(source='usuario.email')

    class Meta:
        model = Portafolio
        fields = '__all__'
        read_only_fields = ['usuario', 'fecha_creacion', 'fecha_modificacion']


class IndiceRiesgoSerializer(serializers.ModelSerializer):
    """
    Serializador para el Índice de Riesgo País Compuesto (IRPC) y su desglose en JSON.
    """
    pais_nombre = serializers.ReadOnlyField(source='pais.nombre')

    class Meta:
        model = IndiceRiesgo
        fields = '__all__'


class AlertaSerializer(serializers.ModelSerializer):
    """
    Serializador para el sistema de alertas automáticas a usuarios.
    """
    pais_nombre = serializers.ReadOnlyField(source='pais.nombre')

    class Meta:
        model = Alerta
        fields = '__all__'


class LogActividadSerializer(serializers.ModelSerializer):
    """
    Serializador para el registro de auditoría del sistema.
    """
    usuario_email = serializers.ReadOnlyField(source='usuario.email')

    class Meta:
        model = LogActividad
        fields = '__all__'