from datetime import datetime, date
from typing import Dict, List, Optional
from pydantic import BaseModel


class RutaFlota(BaseModel):
    """Estado y avance de una ruta en el dashboard de flota."""
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
    avance_porcentaje: float  # % de paradas gestionadas (entregadas + fallidas)
    fecha_creacion: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None


class FlotaResponse(BaseModel):
    """Listado de rutas para el tablero de flota."""
    total_rutas: int
    rutas: List[RutaFlota]


class ResumenResponse(BaseModel):
    """KPIs globales del día para el dashboard."""
    total_pedidos: int
    pedidos_por_estado: Dict[str, int]
    total_rutas: int
    rutas_activas: int
    rutas_finalizadas: int


class ParadaMapa(BaseModel):
    """Parada de entrega del conductor para el mapa."""
    latitud: float
    longitud: float
    destinatario: Optional[str] = None
    secuencia: Optional[int] = None
    estado: Optional[str] = None  # estado_entrega de la parada


class ClienteMapa(BaseModel):
    """Punto de recojo (cliente corporativo) para el mapa."""
    latitud: float
    longitud: float
    razon_social: Optional[str] = None
    secuencia: Optional[int] = None


class ConductorUbicacion(BaseModel):
    """Posicion de un conductor activo con sus paradas y puntos de recojo."""
    conductor_id: int
    conductor: Optional[str] = None
    ruta: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    actualizado_en: Optional[datetime] = None
    en_linea: bool = False  # True si la ultima senal es reciente (< 2 min)
    pausado: bool = False  # tiene una incidencia (auxilio mecanico) abierta
    paradas: List[ParadaMapa] = []
    clientes: List[ClienteMapa] = []


class ClienteSeguimiento(BaseModel):
    """Resumen de pedidos de una empresa cliente clasificados por estado."""
    cliente: str
    total: int
    entregados: int
    fallidos: int
    cancelados: int = 0
    pendientes: int
    en_proceso: int  # ASIGNADO + EN_RUTA


class LiquidacionRequest(BaseModel):
    """Solicitud de liquidacion de un cliente. Recibe cliente y periodo opcional."""
    cliente: str
    periodo_inicio: Optional[date] = None
    periodo_fin: Optional[date] = None


class LiquidacionResponse(BaseModel):
    """Confirmacion de liquidacion generada con URL de descarga autenticada."""
    mensaje: str
    cliente: str
    total_pedidos: int
    liquidacion_id: int
    descarga_url: str
    archivo: str


class EventoHistorial(BaseModel):
    """Un evento en la linea de tiempo de un pedido."""
    evento: str
    descripcion: str
    fecha: Optional[datetime] = None
    realizado_por: Optional[str] = None


class HistorialPedidoResponse(BaseModel):
    """Trazabilidad completa de un pedido con su linea de tiempo."""
    codigo: Optional[str] = None
    cliente_origen: str
    direccion_destino: str
    distrito: Optional[str] = None
    estado_actual: str
    ruta_asignada: Optional[str] = None
    conductor_asignado: Optional[str] = None
    secuencia: Optional[int] = None
    url_evidencia: Optional[str] = None
    motivo_fallo: Optional[str] = None
    eventos: List[EventoHistorial]


class EficienciaConductor(BaseModel):
    """Eficiencia acumulada de un conductor sumando sus rutas cerradas."""
    conductor_id: int
    nombre: Optional[str] = None
    km_recorridos: float
    km_ahorrados: float
    litros_ahorrados: float
    soles_ahorrados: float
