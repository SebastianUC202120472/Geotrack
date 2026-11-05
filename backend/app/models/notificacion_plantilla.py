from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, UniqueConstraint
from app.db.database import Base


class NotificacionPlantilla(Base):
    """Configuración de plantillas editables por evento y canal desde el panel."""

    __tablename__ = "notificaciones_plantillas"
    __table_args__ = (
        UniqueConstraint("evento", "canal", name="uq_notif_plantilla_evento_canal"),
    )

    id = Column(Integer, primary_key=True, index=True)
    evento = Column(String(50), nullable=False, index=True)
    canal = Column(String(20), nullable=False)  # whatsapp | telegram | correo
    asunto = Column(String(200), nullable=True)  # solo correo
    cuerpo = Column(Text, nullable=False)
    activo = Column(Boolean, default=True, nullable=False)
    actualizado_en = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class NotificacionBaja(Base):
    """Registro de bajas y consentimiento (Ley 29733: STOP / opt-out)."""

    __tablename__ = "notificaciones_bajas"

    id = Column(Integer, primary_key=True, index=True)
    canal = Column(String(20), nullable=False)  # whatsapp | telegram
    valor = Column(String(120), nullable=False, index=True)  # teléfono o telegram_chat_id
    motivo = Column(String(50), default="STOP", nullable=False)
    creado_en = Column(DateTime, default=datetime.utcnow, nullable=False)
