from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class AdjuntoResponse(BaseModel):
    id: int
    nombre_archivo: str
    content_type: Optional[str] = None
    tamano: int = 0

    class Config:
        from_attributes = True


class MensajeResponse(BaseModel):
    id: int
    direccion: str            # ENTRANTE | SALIENTE
    remitente: str
    destinatario: Optional[str] = None
    asunto: Optional[str] = None
    cuerpo: Optional[str] = None
    fecha: Optional[datetime] = None
    leido: bool
    adjuntos: List[AdjuntoResponse] = []

    class Config:
        from_attributes = True


class ConversacionResumen(BaseModel):
    """Fila del listado de la bandeja (sin los mensajes completos)."""
    id: int
    contraparte_email: str
    contraparte_nombre: Optional[str] = None
    asunto: str
    estado: str
    no_leidos: int
    ultimo_mensaje_en: Optional[datetime] = None

    class Config:
        from_attributes = True


class ConversacionDetalle(ConversacionResumen):
    """Conversación con todos sus mensajes (vista del hilo)."""
    mensajes: List[MensajeResponse] = []


class ResponderRequest(BaseModel):
    cuerpo: str


class SyncResponse(BaseModel):
    """Resultado de revisar la bandeja por IMAP."""
    mensaje: str
    nuevos: int = 0
