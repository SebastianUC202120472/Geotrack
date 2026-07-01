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


class ZonaItem(BaseModel):
    """Una zona operativa: distrito + cantidad de pedidos."""
    distrito: Optional[str] = None
    total_pedidos: int


class ZonasResponse(BaseModel):
    """Agrupacion de pedidos por distrito."""
    zonas_operativas: List[ZonaItem]


class UbicacionManualRequest(BaseModel):
    """Entrada para fijar manualmente la ubicacion de un pedido. Recibe lat/lng y direccion opcional."""
    model_config = ConfigDict(allow_inf_nan=False)

    latitud: float = Field(ge=-90, le=90)
    longitud: float = Field(ge=-180, le=180)
    direccion: Optional[str] = None


class BuscarDireccionResponse(BaseModel):
    """Resultado de geocodificar un texto de busqueda."""
    encontrado: bool
    latitud: Optional[float] = None
    longitud: Optional[float] = None
