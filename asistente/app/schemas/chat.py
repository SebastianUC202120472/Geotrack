from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.config import settings

_CONTROL = {chr(c) for c in range(32)} - {"\n", "\t"}


class ChatRequest(BaseModel):
    """Pregunta del usuario. Recibe el mensaje, la conversacion (opcional) y si vino por voz."""
    mensaje: str = Field(min_length=1)
    conversacion_id: Optional[str] = Field(default=None, pattern=r"^[a-f0-9]{32}$")
    origen: Literal["texto", "voz"] = "texto"

    @field_validator("mensaje")
    @classmethod
    def _v_mensaje(cls, v: str) -> str:
        v = "".join(c for c in v if c not in _CONTROL).strip()
        if not v:
            raise ValueError("El mensaje está vacío")
        if len(v) > settings.ASISTENTE_MAX_CARACTERES:
            raise ValueError(f"El mensaje supera los {settings.ASISTENTE_MAX_CARACTERES} caracteres")
        return v


class TranscripcionResponse(BaseModel):
    """Texto que se entendio del mensaje de voz."""
    texto: str


class EstadoResponse(BaseModel):
    """Lo que el widget necesita saber para mostrarse."""
    activo: bool
    voz_servidor: bool
    max_caracteres: int
    max_seg_voz: int
    acciones: bool = False


class ResultadoAccion(BaseModel):
    """Resultado de confirmar o cancelar una accion propuesta."""
    id: str
    estado: str
    mensaje: str


class ConversacionItem(BaseModel):
    """Fila del historial de conversaciones."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    titulo: str
    actualizada_en: datetime


class MensajeItem(BaseModel):
    """Un mensaje guardado de la conversacion."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    rol: str
    contenido: str
    origen: str
    bloques: Optional[list] = None
    creado_en: datetime


class ConversacionDetalle(ConversacionItem):
    """Conversacion con sus mensajes."""
    mensajes: list[MensajeItem] = []
