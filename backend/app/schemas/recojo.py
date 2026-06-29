# app/schemas/recojo.py
# Moldes de datos del módulo Inbound de recojos para la API.
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


# --- CUS-10: alta de solicitud (admin) ---
class SolicitudRecojoCreate(BaseModel):
    """ENTRADA (CUS-10): datos del formulario de nueva solicitud de recojo."""
    cliente_id: int
    direccion_origen: str
    volumen_estimado_m3: Optional[float] = None
    contacto_origen: Optional[str] = None
    referencia: Optional[str] = None
    conversacion_id: Optional[int] = None  # si nace desde la Bandeja


class SolicitudRecojoUpdate(BaseModel):
    """ENTRADA (CUS-10): campos editables mientras la solicitud está SOLICITADO."""
    direccion_origen: Optional[str] = None
    volumen_estimado_m3: Optional[float] = None
    contacto_origen: Optional[str] = None
    referencia: Optional[str] = None


class SolicitudRecojoResponse(BaseModel):
    """SALIDA: una solicitud de recojo completa."""
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


# --- CUS-11: asignar ruta de recojo (admin) ---
class AsignarRutaRecojoRequest(BaseModel):
    """ENTRADA (CUS-11): solicitudes a agrupar + conductor + vehículo."""
    recojo_ids: List[int]
    conductor_id: int
    vehiculo_placa: str
    nombre_ruta: Optional[str] = None


class AsignarRutaRecojoResponse(BaseModel):
    """SALIDA (CUS-11): confirmación con el id y código de la ruta creada."""
    mensaje: str
    ruta_id: int
    codigo: Optional[str] = None


# --- CUS-12: manifiesto y recepción (conductor) ---
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
    """SALIDA (CUS-12): la ruta de recojo y sus puntos ordenados por secuencia."""
    ruta_id: int
    codigo: Optional[str] = None
    nombre: str
    estado: str
    total_paradas: int
    paradas: List[ParadaRecojo]


class RecepcionResponse(BaseModel):
    """SALIDA (CUS-12): resultado de registrar la recepción condicionada."""
    recojo_id: int
    codigo: Optional[str] = None
    estado: str
    cantidad_declarada: Optional[int] = None
    url_guia: Optional[str] = None
    fecha_recojo: Optional[datetime] = None
    mensaje: str


# --- Aceptar solicitud con Excel (admin) ---
class AceptarSolicitudResponse(BaseModel):
    """SALIDA: resultado de aceptar una solicitud de recojo y crear sus pedidos POR_RECOGER."""
    recojo_id: int
    codigo: str
    pedidos_creados: int
    pedidos_geocodificados: int
    pedidos_sin_ubicar: int
    # True cuando la geocodificación quedó corriendo en segundo plano (carga masiva): al
    # responder ningún pedido tiene coordenadas todavía, se van ubicando en los minutos siguientes.
    geocodificacion_en_segundo_plano: bool = False
    filas_rechazadas: list[str]


# --- Armado de ruta de recojo (almacén, CUS-11) ---
class SolicitudArmarItem(BaseModel):
    """SALIDA: solicitud de recojo SOLICITADO para la vista de armado de ruta del almacén."""
    id: int
    codigo: Optional[str] = None
    cliente_origen: str
    direccion_origen: str
    distrito: Optional[str] = None
    num_pedidos: int

    class Config:
        from_attributes = True
