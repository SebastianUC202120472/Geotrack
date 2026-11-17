# Acciones propuestas por el asistente y derivaciones a una persona (tablas propias).
# - Accion: registro (auditoria y metricas) de cada reprogramacion o contacto que el asistente
#   PROPUSO y de lo que decidio el visitante. Solo guarda un resumen enmascarado; los datos reales
#   viven en memoria hasta el clic y van directo a la API del portal.
# - Derivacion: bandeja propia del modulo. Cuando el visitante pide una persona o el asistente no
#   logra resolver, la conversacion queda aqui para que el equipo la atienda.
# Ambas se borran junto con su conversacion (retencion, Ley 29733).
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from app.core.fechas import ahora_utc
from app.db.database import Base


class Accion(Base):
    """Una accion propuesta al visitante y su resultado."""
    __tablename__ = "accion"

    id = Column(String(32), primary_key=True)
    conversacion_id = Column(String(32), ForeignKey("conversacion.id", ondelete="CASCADE"), nullable=False, index=True)
    tipo = Column(String(20), nullable=False)          # reprogramar | contacto
    estado = Column(String(20), nullable=False, default="PENDIENTE")   # PENDIENTE | CONFIRMADA | CANCELADA | VENCIDA | ERROR
    resumen = Column(String(300), nullable=False)      # enmascarado
    resultado = Column(String(300), nullable=True)
    creada_en = Column(DateTime, nullable=False, default=ahora_utc, index=True)
    resuelta_en = Column(DateTime, nullable=True)


class Derivacion(Base):
    """Una conversacion que pide atencion de una persona del equipo."""
    __tablename__ = "derivacion"

    id = Column(Integer, primary_key=True)
    conversacion_id = Column(String(32), ForeignKey("conversacion.id", ondelete="CASCADE"), nullable=False, index=True)
    origen = Column(String(20), nullable=False)        # visitante (boton) | asistente (funcion)
    motivo = Column(String(300), nullable=False)       # enmascarado
    # Medio para devolver el contacto, solo si el visitante lo dio para eso. Es el unico dato
    # personal en claro del modulo; se borra con la conversacion.
    contacto = Column(String(120), nullable=True)
    idioma = Column(String(2), nullable=False, default="es")
    estado = Column(String(20), nullable=False, default="PENDIENTE")   # PENDIENTE | ATENDIDA
    creada_en = Column(DateTime, nullable=False, default=ahora_utc, index=True)
    atendida_por = Column(String(120), nullable=True)
    atendida_en = Column(DateTime, nullable=True)
