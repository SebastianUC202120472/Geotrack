from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


def _texto_opcional(v: Optional[str]) -> Optional[str]:
    """Quita espacios y convierte el texto vacio en None. Recibe el texto."""
    if v is None:
        return None
    v = " ".join(str(v).split())
    return v or None


class SolicitudRecojoCreate(BaseModel):
    """Datos para crear una nueva solicitud de recojo. Recibe cliente_id, dirección y opcionales."""
    cliente_id: int
    direccion_origen: str
    volumen_estimado_m3: Optional[float] = None
    contacto_origen: Optional[str] = None
    referencia: Optional[str] = None
    conversacion_id: Optional[int] = None  # si nace desde la Bandeja
    fecha_programada: Optional[date] = None


class PedidoManualIn(BaseModel):
    """Un pedido escrito a mano en el registro manual de una solicitud (C11-02)."""
    referencia_externa: str = Field(..., max_length=50)
    direccion_destino: str = Field(..., max_length=255)
    nombre_destinatario: Optional[str] = Field(None, max_length=120)
    telefono_destinatario: Optional[str] = Field(None, max_length=30)
    dni_destinatario: Optional[str] = Field(None, max_length=20)
    peso_kg: Optional[float] = Field(None, ge=0, le=5000)
    volumen_m3: Optional[float] = Field(None, ge=0, le=100)

    @field_validator("referencia_externa", "direccion_destino")
    @classmethod
    def _v_obligatorio(cls, v: str) -> str:
        v = _texto_opcional(v)
        if not v:
            raise ValueError("Este dato es obligatorio")
        return v

    @field_validator("nombre_destinatario", "telefono_destinatario", "dni_destinatario")
    @classmethod
    def _v_opcional(cls, v: Optional[str]) -> Optional[str]:
        return _texto_opcional(v)


class SolicitudManualCreate(BaseModel):
    """Solicitud registrada a mano (cliente que pide por telefono) con sus pedidos (C11-02)."""
    cliente_id: int
    referencia: Optional[str] = Field(None, max_length=120)
    contacto_origen: Optional[str] = Field(None, max_length=100)
    fecha_programada: Optional[date] = None
    pedidos: List[PedidoManualIn] = Field(..., min_length=1, max_length=500)


class SolicitudRecojoUpdate(BaseModel):
    """Campos editables de una solicitud en estado SOLICITADO (C11-03)."""
    direccion_origen: Optional[str] = None
    volumen_estimado_m3: Optional[float] = None
    contacto_origen: Optional[str] = None
    referencia: Optional[str] = None
    fecha_programada: Optional[date] = None


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
    fecha_programada: Optional[date] = None
    motivo_no_realizado: Optional[str] = None
    intentos_no_realizados: Optional[int] = 0
    num_pedidos: Optional[int] = None

    class Config:
        from_attributes = True


class AsignarRutaRecojoRequest(BaseModel):
    """Datos para asignar una ruta de recojo. Recibe lista de recojos, conductor y nombre opcional.
    La placa sale del vehiculo vinculado al conductor (C12-01); vehiculo_placa se ignora."""
    recojo_ids: List[int]
    conductor_id: int
    vehiculo_placa: Optional[str] = None
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
    estado: str  # SOLICITADO | ASIGNADO | EN_RUTA | RECOGIDO | NO_REALIZADO
    cantidad_declarada: Optional[int] = None
    url_guia: Optional[str] = None
    contacto_origen: Optional[str] = None
    motivo_no_realizado: Optional[str] = None
    num_pedidos: int = 0


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


class NoRealizadoRequest(BaseModel):
    """Motivo por el que el conductor no pudo hacer el recojo (C12-02)."""
    motivo: str = Field(..., min_length=3, max_length=200)

    @field_validator("motivo")
    @classmethod
    def _v_motivo(cls, v: str) -> str:
        v = " ".join(v.split())
        if len(v) < 3:
            raise ValueError("Indica el motivo (al menos 3 caracteres)")
        return v


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
    """Solicitud de recojo en estado SOLICITADO para la vista de armado de ruta (con mapa y volumen, C12-03)."""
    id: int
    codigo: Optional[str] = None
    cliente_origen: str
    direccion_origen: str
    distrito: Optional[str] = None
    num_pedidos: int
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    volumen_m3: float = 0.0          # volumen de sus pedidos (o el estimado si no lo traen)
    peso_kg: float = 0.0
    fecha_programada: Optional[date] = None
    referencia: Optional[str] = None
    contacto_origen: Optional[str] = None
    motivo_no_realizado: Optional[str] = None
    intentos_no_realizados: int = 0

    class Config:
        from_attributes = True


class RutaRecojoItem(BaseModel):
    """Ruta de recojo para el almacen: avance y datos del conductor (C22-02)."""
    ruta_id: int
    codigo: Optional[str] = None
    nombre: str
    estado: str
    conductor: Optional[str] = None
    vehiculo_placa: Optional[str] = None
    total_paradas: int
    recogidas: int
    no_realizadas: int
    fecha_creacion: datetime
