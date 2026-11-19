export type RolUsuario = 'ADMIN' | 'ANALISTA' | 'VIEWER';
export type NivelRiesgo = 'BAJO' | 'MODERADO' | 'ALTO' | 'CRITICO';
export type SeveridadAlerta = 'INFO' | 'WARNING' | 'CRITICAL';

export interface Usuario {
    id: number;
    email: string;
    nombre_completo: string;
    rol: RolUsuario;
    activo?: boolean;
}

export interface AuthResponse {
    access: string;
    refresh: string;
    user: Usuario;
}

export interface Pais {
    id: number;
    codigo_iso: string;
    nombre: string;
    region: string;
    moneda_codigo: string;
    moneda_nombre: string;
    poblacion: number;
    activo: boolean;
}

export interface IndicadorEconomico {
    id: number;
    pais: number;
    pais_nombre: string;
    tipo: string;
    anio: number;
    valor: number;
    unidad: string;
    fuente: string;
}

export interface TipoCambio {
    id: number;
    moneda_origen: string;
    moneda_destino: string;
    fecha: string;
    tasa: number;
    variacion_porcentual: number;
}

export interface IndiceRiesgo {
    id: number;
    pais: number;
    pais_nombre: string;
    fecha_calculo: string;
    score_economico: number;
    score_cambiario: number;
    score_estabilidad: number;
    indice_compuesto: number;
    nivel_riesgo: NivelRiesgo;
    detalle_calculo: any;
    historico?: IndiceRiesgo[];
}

export interface Alerta {
    id: number;
    pais: number | null;
    pais_nombre?: string;
    tipo_alerta: string;
    severidad: SeveridadAlerta;
    titulo: string;
    mensaje: string;
    leida: boolean;
    fecha_creacion: string;
}

export interface Posicion {
    id?: number;
    portafolio?: number;
    pais: number;
    pais_nombre?: string;
    sector: string;
    monto_inversion_usd: number;
    fecha_entrada: string;
    fecha_salida?: string | null;
    notas?: string;
}

export interface Portafolio {
    id: number;
    usuario: number;
    usuario_email: string;
    nombre: string;
    descripcion: string;
    es_publico: boolean;
    activo: boolean;
    fecha_creacion: string;
    posiciones: Posicion[];
}

export interface DashboardResumen {
    kpis: {
        paises_monitoreados: number;
        irpc_promedio_regional: number;
        portafolios_activos: number;
        capital_total_invertido_usd: number;
        alertas_pendientes: number;
    };
    destacados: {
        menor_riesgo: { pais: string; codigo_iso: string; irpc: number } | null;
        mayor_riesgo: { pais: string; codigo_iso: string; irpc: number } | null;
    };
    distribucion_riesgo: {
        BAJO: number;
        MODERADO: number;
        ALTO: number;
        CRITICO: number;
    };
}