from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship

from app.db.database import Base


class Conversacion(Base):
    """Hilo de correo con un cliente."""
    __tablename__ = "correo_conversaciones"

    id = Column(Integer, primary_key=True, index=True)
    contraparte_email = Column(String(255), index=True, nullable=False)  # con quién se conversa
    contraparte_nombre = Column(String(150), nullable=True)
    asunto = Column(String(300), nullable=False)
    asunto_normalizado = Column(String(300), index=True, nullable=False)  # sin "Re:"/"Fwd:" (para agrupar)
    estado = Column(String(20), default="PENDIENTE")  # PENDIENTE | ATENDIDA
    no_leidos = Column(Integer, default=0)            # mensajes entrantes sin abrir
    ultimo_mensaje_en = Column(DateTime, default=datetime.utcnow, index=True)
    creado_en = Column(DateTime, default=datetime.utcnow)

    mensajes = relationship(
        "MensajeCorreo",
        back_populates="conversacion",
        order_by="MensajeCorreo.fecha",
        cascade="all, delete-orphan",
    )


class MensajeCorreo(Base):
    """Un mensaje dentro de una conversación (entrante o saliente)."""
    __tablename__ = "correo_mensajes"

    id = Column(Integer, primary_key=True, index=True)
    conversacion_id = Column(Integer, ForeignKey("correo_conversaciones.id"), nullable=False, index=True)
    direccion = Column(String(10), nullable=False)   # ENTRANTE (cliente -> nosotros) | SALIENTE
    remitente = Column(String(255), nullable=False)
    destinatario = Column(String(255), nullable=True)
    asunto = Column(String(300), nullable=True)
    cuerpo = Column(Text, nullable=True)
    fecha = Column(DateTime, default=datetime.utcnow, index=True)
    message_id = Column(String(400), index=True, nullable=True)  # Message-ID del correo (evita duplicados)
    in_reply_to = Column(String(400), nullable=True)             # para enlazar el hilo en el cliente de correo
    leido = Column(Boolean, default=False)
    enviado_por = Column(Integer, nullable=True)                 # id del admin que respondió (salientes)

    conversacion = relationship("Conversacion", back_populates="mensajes")
    adjuntos = relationship(
        "MensajeAdjunto",
        back_populates="mensaje",
        cascade="all, delete-orphan",
    )


class MensajeAdjunto(Base):
    """Adjunto de un mensaje; contenido guardado en BD (no expuesto como archivo estático)."""
    __tablename__ = "correo_adjuntos"

    id = Column(Integer, primary_key=True, index=True)
    mensaje_id = Column(Integer, ForeignKey("correo_mensajes.id"), nullable=False, index=True)
    nombre_archivo = Column(String(255), nullable=False)
    content_type = Column(String(120), nullable=True)
    tamano = Column(Integer, default=0)          # bytes
    contenido = Column(LargeBinary, nullable=False)

    mensaje = relationship("MensajeCorreo", back_populates="adjuntos")
