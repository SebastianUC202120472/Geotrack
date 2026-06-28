# app/schemas/notificacion.py
# Modelos de respuesta para el feed de notificaciones del panel admin.
from pydantic import BaseModel


class ItemNotificacion(BaseModel):
    """Un aviso accionable con su contador y la ruta a la que navega el panel."""
    tipo: str       # "reportes" | "incidencias" | "recojos" | "correos" | "restablecimientos"
    etiqueta: str   # texto legible, p.ej. "Reportes de entrega"
    count: int
    ruta: str       # a dónde navega el panel, p.ej. "/pedidos"


class NotificacionesResponse(BaseModel):
    """Respuesta del endpoint de notificaciones: total accionable + detalle por tipo."""
    total: int
    items: list[ItemNotificacion]
