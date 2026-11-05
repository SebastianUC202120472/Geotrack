"""Modelos de dominio del centro de notificaciones: mensaje canonico agnostico al proveedor."""
from dataclasses import dataclass, field
from enum import Enum


class Canal(str, Enum):
    """Canales soportados; agregar uno nuevo no exige tocar el resto del modulo."""
    TELEGRAM = "telegram"
    CORREO = "correo"
    WHATSAPP = "whatsapp"


class Prioridad(str, Enum):
    """Urgente atraviesa el horario silencioso; normal espera a la manana."""
    NORMAL = "normal"
    URGENTE = "urgente"


@dataclass(frozen=True)
class Destinatario:
    """A quien va el aviso; 'valor' es chat_id de Telegram o correo segun el canal."""
    tipo: str
    valor: str
    nombre: str | None = None


@dataclass(frozen=True)
class Mensaje:
    """Mensaje canonico: el canal decide como entregarlo, la fila guarda su estado."""
    evento: str
    canal: Canal
    destinatario: Destinatario
    cuerpo: str
    clave_idempotencia: str
    asunto: str | None = None
    prioridad: Prioridad = Prioridad.NORMAL
    metadatos: dict = field(default_factory=dict)
    notificacion_id: int | None = None
