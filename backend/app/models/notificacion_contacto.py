from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, UniqueConstraint

from app.db.database import Base


class NotificacionContacto(Base):
    """Contacto externo habilitado para recibir una notificacion por un canal."""

    __tablename__ = "notificaciones_contactos"
    __table_args__ = (
        UniqueConstraint("entidad_tipo", "entidad_id", "canal", name="uq_notif_contacto_entidad_canal"),
    )

    id = Column(Integer, primary_key=True, index=True)
    entidad_tipo = Column(String(40), nullable=False, index=True)
    entidad_id = Column(Integer, nullable=False, index=True)
    canal = Column(String(20), nullable=False)
    valor = Column(String(120), nullable=False)
    nombre = Column(String(120), nullable=True)
    activo = Column(Boolean, nullable=False, default=True)
    creado_en = Column(DateTime, default=datetime.utcnow, nullable=False)
