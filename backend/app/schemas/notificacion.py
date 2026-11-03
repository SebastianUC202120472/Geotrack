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


class NotificacionContactoCreate(BaseModel):
    """Contacto de un destinatario para un canal externo."""
    entidad_tipo: str
    entidad_id: int
    canal: str = "telegram"
    valor: str
    nombre: str | None = None
    activo: bool = True
