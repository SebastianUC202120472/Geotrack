from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class PedidoResponse(BaseModel):
    """Esquema de salida de un pedido con todos sus campos."""
    id: int
    codigo: Optional[str] = None
    referencia_externa: Optional[str] = None
    cliente_id: Optional[int] = None
    cliente_origen: str
    direccion_destino: str
    nombre_destinatario: Optional[str] = None
    telefono_destinatario: Optional[str] = None
    dni_destinatario: Optional[str] = None
    distrito: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    peso_kg: Optional[float] = None
    volumen_m3: Optional[float] = None
    estado: str
    fecha_creacion: Optional[datetime] = None
    fecha_entrega: Optional[datetime] = None
    recojo_id: Optional[int] = None
    validado_en: Optional[datetime] = None
    motivo_cancelacion: Optional[str] = None
    ruta_nombre: Optional[str] = None
    conductor_nombre: Optional[str] = None

    class Config:
        from_attributes = True  # se construye desde el objeto SQLAlchemy


class CargaPedidosResponse(BaseModel):
    """Resultado de la carga masiva de pedidos por Excel."""
    mensaje: str
    pedidos_nuevos: int
    total_filas_leidas: int
    pedidos_geocodificados: int = 0
    pedidos_fallidos: int = 0
    rechazados: List[dict] = []
    total_rechazados: int = 0


class GeocodificacionResponse(BaseModel):
    """Resultado del proceso de geocodificacion de pedidos."""
    mensaje: str
    pedidos_exitosos: int = 0
    pedidos_fallidos: int = 0
    pedidos_restantes: int = 0  # quedan para la siguiente tanda (C16-03)


class ZonaItem(BaseModel):
    """Una zona operativa: distrito + cantidad de pedidos."""
    distrito: Optional[str] = None
    total_pedidos: int


class ZonasResponse(BaseModel):
    """Agrupacion de pedidos por distrito."""
    zonas_operativas: List[ZonaItem]


class ZonaPorEnrutarItem(BaseModel):
    """Una zona con pedidos por enrutar: distrito + pendientes + asignados."""
    distrito: str
    pendientes: int
    asignados: int


class ZonasPorEnrutarResponse(BaseModel):
    """Zonas con pedidos pendientes o asignados, calculadas en el servidor."""
    zonas: List[ZonaPorEnrutarItem]


class UbicacionManualRequest(BaseModel):
    """Entrada para fijar manualmente la ubicacion de un pedido. Recibe lat/lng y direccion opcional."""
    model_config = ConfigDict(allow_inf_nan=False)

    latitud: float = Field(ge=-90, le=90)
    longitud: float = Field(ge=-180, le=180)
    direccion: Optional[str] = None


class CoincidenciaDireccion(BaseModel):
    """Un lugar posible para el texto buscado (C17-02)."""
    direccion: str
    latitud: float
    longitud: float
    distrito: Optional[str] = None


class BuscarDireccionResponse(BaseModel):
    """Resultado de geocodificar un texto de busqueda: la primera coincidencia y la lista completa."""
    encontrado: bool
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    coincidencias: List[CoincidenciaDireccion] = []


class CancelarPedidoRequest(BaseModel):
    """Motivo obligatorio para cancelar un pedido (C31-02)."""
    motivo: str = Field(..., max_length=255)


class AtenderReprogramacionRequest(BaseModel):
    """Decision del admin sobre la solicitud de reprogramacion del cliente. Recibe aceptar y nota."""
    aceptar: bool
    nota: Optional[str] = Field(None, max_length=255)


class SolicitudReprogramacionResponse(BaseModel):
    """Solicitud de reprogramacion hecha desde el portal (C43-01)."""
    id: int
    pedido_id: int
    franja: str
    estado: str
    creado_en: Optional[datetime] = None
    respuesta: Optional[str] = None
    atendida_en: Optional[datetime] = None
