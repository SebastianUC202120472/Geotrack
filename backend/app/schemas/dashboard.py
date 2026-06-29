# app/schemas/dashboard.py
# Define los "moldes" de salida del módulo de TRAZABILIDAD (Fase 4).
from datetime import datetime, date
from typing import Dict, List, Optional
from pydantic import BaseModel


# CUS-33: Seguimiento en vivo de la flota
class RutaFlota(BaseModel):
    """Estado y avance de UNA ruta dentro del dashboard de flota."""
    ruta_id: int
    nombre: str
    estado: str  # CREADA, EN_PROGRESO, FINALIZADA
    conductor_id: Optional[int] = None
    conductor_nombre: Optional[str] = None
    vehiculo_placa: Optional[str] = None
    total_paradas: int
    entregadas: int
    fallidas: int
    pendientes: int
    avance_porcentaje: float  # % de paradas ya gestionadas (entregadas + fallidas)
    fecha_creacion: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None


class FlotaResponse(BaseModel):
    """Listado completo de rutas para el tablero de la flota."""
    total_rutas: int
    rutas: List[RutaFlota]


class ResumenResponse(BaseModel):
    """KPIs globales del día (tarjetas del dashboard)."""
    total_pedidos: int
    pedidos_por_estado: Dict[str, int]  # ej. {"LISTO_PARA_ENVIO": 2, "ENTREGADO": 3}
    total_rutas: int
    rutas_activas: int
    rutas_finalizadas: int


# Mapa de flota en tiempo real
class ParadaMapa(BaseModel):
    """Una parada de ENTREGA pendiente del conductor (icono de pedido), para el mapa."""
    latitud: float
    longitud: float
    destinatario: Optional[str] = None
    secuencia: Optional[int] = None


class ClienteMapa(BaseModel):
    """Un punto de recojo = ubicación del cliente corporativo (icono distinto, mapa de almacén)."""
    latitud: float
    longitud: float
    razon_social: Optional[str] = None
    secuencia: Optional[int] = None


class ConductorUbicacion(BaseModel):
    """Posición de un conductor con ruta activa, sus paradas de entrega (pedidos) y/o
    sus puntos de recojo (clientes corporativos)."""
    conductor_id: int
    conductor: Optional[str] = None
    ruta: Optional[str] = None
    latitud: Optional[float] = None       # None si aún no envió señal
    longitud: Optional[float] = None
    actualizado_en: Optional[datetime] = None
    en_linea: bool = False                # True si la última señal es reciente (< 2 min)
    pausado: bool = False  # CUS-30: tiene una incidencia (auxilio mecánico) abierta
    paradas: List[ParadaMapa] = []        # entregas (icono de pedido)
    clientes: List[ClienteMapa] = []      # recojos: ubicación del cliente corporativo


# Seguimiento de repartos agregado por empresa cliente (no por ruta).
class ClienteSeguimiento(BaseModel):
    """Resumen de los pedidos de UNA empresa cliente, clasificados por grupo.
    Los cuatro grupos suman el total."""
    cliente: str
    total: int
    entregados: int
    fallidos: int
    pendientes: int
    en_proceso: int  # ASIGNADO + EN_RUTA


# CUS-36: liquidación por cliente
class LiquidacionRequest(BaseModel):
    """ENTRADA (CUS-36): el admin pide la liquidación de un cliente. El período es
    opcional; si no se envía, se incluyen todos los pedidos del cliente."""
    cliente: str
    periodo_inicio: Optional[date] = None
    periodo_fin: Optional[date] = None


class LiquidacionResponse(BaseModel):
    """SALIDA (CUS-36): confirmación + ruta del endpoint AUTENTICADO de descarga.
    El .xlsx no es público (contiene datos personales): se baja con token de admin."""
    mensaje: str
    cliente: str
    total_pedidos: int
    liquidacion_id: int
    descarga_url: str  # relativo a /api, p.ej. /dashboard/liquidaciones/3/descarga
    archivo: str


# CUS-35: Historial / línea de tiempo de un paquete
class EventoHistorial(BaseModel):
    """Un punto en la línea de tiempo del paquete (fila de historial_pedidos)."""
    evento: str                       # estado al que cambió (ej. "ENTREGADO")
    descripcion: str                  # explicación legible
    fecha: Optional[datetime] = None  # cuándo ocurrió
    realizado_por: Optional[str] = None  # correo del usuario que hizo el cambio


class HistorialPedidoResponse(BaseModel):
    """Trazabilidad completa de un paquete (CUS-35)."""
    codigo: Optional[str] = None  # PD-001
    cliente_origen: str
    direccion_destino: str
    distrito: Optional[str] = None
    estado_actual: str
    ruta_asignada: Optional[str] = None
    conductor_asignado: Optional[str] = None  # nombre del conductor de la ruta
    secuencia: Optional[int] = None
    url_evidencia: Optional[str] = None
    motivo_fallo: Optional[str] = None
    eventos: List[EventoHistorial]  # la línea de tiempo, en orden cronológico


# CUS-34: eficiencia acumulada por conductor (Km y ahorro de combustible).
class EficienciaConductor(BaseModel):
    """Resumen de eficiencia de UN conductor, sumando sus rutas ya cerradas."""
    conductor_id: int
    nombre: Optional[str] = None
    km_recorridos: float
    km_ahorrados: float
    litros_ahorrados: float
    soles_ahorrados: float
