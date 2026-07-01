from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class SolicitudRecojoCreate(BaseModel):
    """Datos para crear una nueva solicitud de recojo. Recibe cliente_id, dirección y opcionales."""
    cliente_id: int
    direccion_origen: str
    volumen_estimado_m3: Optional[float] = None
    contacto_origen: Optional[str] = None
    referencia: Optional[str] = None
    conversacion_id: Optional[int] = None  # si nace desde la Bandeja


class SolicitudRecojoUpdate(BaseModel):
    """Campos editables de una solicitud en estado SOLICITADO."""
    direccion_origen: Optional[str] = None
    volumen_estimado_m3: Optional[float] = None
    contacto_origen: Optional[str] = None
    referencia: Optional[str] = None


class SolicitudRecojoResponse(BaseModel):
    """Solicitud de recojo completa devuelta por la API."""
    id: int
    codigo: Optional[str] = None
    cliente_id: int
    cliente_origen: str
    direccion_origen: str
    distrito: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    volumen_estimado_m3: Optional[float] = None
    contacto_origen: Optional[str] = None
    referencia: Optional[str] = None
    estado: str
    cantidad_declarada: Optional[int] = None
    url_guia: Optional[str] = None
    ruta_id: Optional[int] = None
    secuencia: Optional[int] = None
    conversacion_id: Optional[int] = None
    fecha_creacion: datetime
    fecha_recojo: Optional[datetime] = None

    class Config:
        from_attributes = True


class AsignarRutaRecojoRequest(BaseModel):
    """Datos para asignar una ruta de recojo. Recibe lista de recojos, conductor y vehículo."""
    recojo_ids: List[int]
    conductor_id: int
    vehiculo_placa: str
    nombre_ruta: Optional[str] = None


class AsignarRutaRecojoResponse(BaseModel):
    """Confirmación de ruta creada con su id y código."""
    mensaje: str
    ruta_id: int
    codigo: Optional[str] = None


class ParadaRecojo(BaseModel):
    """Un punto de origen del manifiesto de recojo."""
    secuencia: int
    recojo_id: int
    codigo: Optional[str] = None
    cliente_origen: str
    direccion_origen: str
    distrito: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    volumen_estimado_m3: Optional[float] = None
    estado: str  # SOLICITADO | ASIGNADO | EN_RUTA | RECOGIDO
    cantidad_declarada: Optional[int] = None
    url_guia: Optional[str] = None


class ManifiestoRecojoResponse(BaseModel):
    """Ruta de recojo con sus paradas ordenadas por secuencia."""
    ruta_id: int
    codigo: Optional[str] = None
    nombre: str
    estado: str
    total_paradas: int
    paradas: List[ParadaRecojo]


class RecepcionResponse(BaseModel):
    """Resultado de registrar la recepción de un punto de recojo."""
    recojo_id: int
    codigo: Optional[str] = None
    estado: str
    cantidad_declarada: Optional[int] = None
    url_guia: Optional[str] = None          # compat: primera foto
    fotos: List[str] = []                   # todas las fotos de evidencia subidas
    fecha_recojo: Optional[datetime] = None
    mensaje: str


class AceptarSolicitudResponse(BaseModel):
    """Resultado de aceptar una solicitud y crear sus pedidos POR_RECOGER desde Excel."""
    recojo_id: int
    codigo: str
    pedidos_creados: int
    pedidos_geocodificados: int
    pedidos_sin_ubicar: int
    geocodificacion_en_segundo_plano: bool = False  # True si la geocodificación sigue corriendo en segundo plano
    filas_rechazadas: list[str]


class SolicitudArmarItem(BaseModel):
    """Solicitud de recojo en estado SOLICITADO para la vista de armado de ruta."""
    id: int
    codigo: Optional[str] = None
    cliente_origen: str
    direccion_origen: str
    distrito: Optional[str] = None
    num_pedidos: int

    class Config:
        from_attributes = True
