# Conversaciones anonimas del chat de atencion (tablas propias).
# Privacidad (Ley 29733): no se guarda la IP (solo su huella HMAC), los mensajes se guardan
# con DNI, telefonos y correos enmascarados, y todo se borra solo pasados ATENCION_RETENCION_DIAS.
from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.fechas import ahora_utc
from app.db.database import Base


class Conversacion(Base):
    """Una conversacion de un visitante del sitio o del portal."""
    __tablename__ = "conversacion"

    id = Column(String(32), primary_key=True)                    # 32 hex aleatorios
    idioma = Column(String(2), nullable=False, default="es")     # ultimo idioma detectado
    pagina = Column(String(20), nullable=False, default="landing")   # landing | portal
    ip_huella = Column(String(64), nullable=False, index=True)
    estado = Column(String(20), nullable=False, default="ABIERTA")   # ABIERTA | DERIVADA
    mensajes_usuario = Column(Integer, nullable=False, default=0)
    privacidad_aceptada_en = Column(DateTime, nullable=False, default=ahora_utc)
    creada_en = Column(DateTime, nullable=False, default=ahora_utc, index=True)
    actualizada_en = Column(DateTime, nullable=False, default=ahora_utc, index=True)

    mensajes = relationship("Mensaje", back_populates="conversacion", cascade="all, delete-orphan",
                            passive_deletes=True, order_by="Mensaje.id")


class Mensaje(Base):
    """Un mensaje de la conversacion (del visitante o del asistente), ya enmascarado."""
    __tablename__ = "mensaje"

    id = Column(Integer, primary_key=True)
    conversacion_id = Column(String(32), ForeignKey("conversacion.id", ondelete="CASCADE"), nullable=False, index=True)
    rol = Column(String(12), nullable=False)                     # usuario | asistente
    contenido = Column(Text, nullable=False)
    origen = Column(String(10), nullable=False, default="texto") # texto | voz
    idioma = Column(String(2), nullable=False, default="es")
    # Como se respondio: ia | sin_ia (respaldo con la base de conocimiento) | bloqueado.
    modo = Column(String(12), nullable=True)
    proveedor = Column(String(40), nullable=True)
    articulos = Column(JSON, nullable=True)                      # claves de articulos usados (metricas)
    alerta_seguridad = Column(String(40), nullable=True)         # p. ej. "cambio_de_reglas"
    creado_en = Column(DateTime, nullable=False, default=ahora_utc, index=True)

    conversacion = relationship("Conversacion", back_populates="mensajes")
