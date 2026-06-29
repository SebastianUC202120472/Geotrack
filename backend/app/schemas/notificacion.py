# app/schemas/notificacion.py
# Esquemas de respuesta para el historial de notificaciones del panel admin.
from datetime import datetime

from pydantic import BaseModel


class NotificacionItem(BaseModel):
    """Un aviso individual con su estado de lectura."""
    id: int
    tipo: str
    titulo: str
    mensaje: str | None
    ruta: str | None
    creado_en: datetime
    visto_en: datetime | None

    class Config:
        from_attributes = True


class NotificacionesResponse(BaseModel):
    """Respuesta del endpoint de notificaciones: contador no vistas + historial."""
    no_vistas: int
    items: list[NotificacionItem]
