from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from app.db.database import Base


class NotificacionCursor(Base):
    """Guarda el último ID o timestamp procesado de las tablas del núcleo.
    Permite al contenedor 'notificador' leer en solo lectura las novedades sin hooks."""

    __tablename__ = "notificaciones_cursores"

    fuente = Column(String(50), primary_key=True)  # historial_pedidos | rutas | incidencias | reclamos | solicitudes_recojo
    ultimo_id = Column(Integer, default=0, nullable=False)
    actualizado_en = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
