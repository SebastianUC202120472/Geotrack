import uuid

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.fechas import ahora_utc
from app.db.database import Base


def _uuid() -> str:
    """Genera un identificador aleatorio para la conversacion. Sin input."""
    return uuid.uuid4().hex


class Conversacion(Base):
    """Conversacion de un usuario del panel con el asistente (historial por usuario)."""

    __tablename__ = "conversaciones"

    id = Column(String(32), primary_key=True, default=_uuid)
    usuario_id = Column(Integer, nullable=False, index=True)   # id del usuario en el nucleo
    titulo = Column(String(120), nullable=False, default="Nueva conversación")
    creada_en = Column(DateTime, default=ahora_utc, nullable=False)
    actualizada_en = Column(DateTime, default=ahora_utc, nullable=False, index=True)

    mensajes = relationship(
        "Mensaje",
        back_populates="conversacion",
        cascade="all, delete-orphan",
        order_by="Mensaje.id",
    )


class Mensaje(Base):
    """Un mensaje de la conversacion: lo que escribio el usuario o lo que respondio el asistente."""

    __tablename__ = "mensajes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversacion_id = Column(String(32), ForeignKey("conversaciones.id", ondelete="CASCADE"), nullable=False, index=True)
    rol = Column(String(12), nullable=False)          # usuario | asistente
    contenido = Column(Text, nullable=False, default="")
    origen = Column(String(10), nullable=False, default="texto")   # texto | voz
    bloques = Column(JSON, nullable=True)             # tablas, graficos y enlaces mostrados
    consultas = Column(JSON, nullable=True)           # funciones que se ejecutaron (nombre + argumentos)
    creado_en = Column(DateTime, default=ahora_utc, nullable=False)

    conversacion = relationship("Conversacion", back_populates="mensajes")
