import secrets

from sqlalchemy import JSON, Column, DateTime, Integer, String, Text

from app.core.fechas import ahora_utc
from app.db.database import Base

# Estados de una propuesta. Solo PENDIENTE puede pasar a EN_CURSO (y una sola vez).
PENDIENTE = "PENDIENTE"
EN_CURSO = "EN_CURSO"
EJECUTADA = "EJECUTADA"
ERROR = "ERROR"
CANCELADA = "CANCELADA"
VENCIDA = "VENCIDA"
INVALIDADA = "INVALIDADA"   # se cambio de conversacion o se borro la conversacion


def _id_aleatorio() -> str:
    """Identificador aleatorio e impredecible de la propuesta. Sin input."""
    return secrets.token_hex(16)


class PropuestaAccion(Base):
    """Accion que el asistente PROPUSO y que solo se ejecuta si el mismo usuario pulsa Confirmar.
    El objetivo (ids del nucleo) lo resolvio el servidor; el modelo nunca elige ruta ni cuerpo."""

    __tablename__ = "propuestas_accion"

    id = Column(String(32), primary_key=True, default=_id_aleatorio)
    usuario_id = Column(Integer, nullable=False, index=True)
    usuario_correo = Column(String(120), nullable=False)
    rol = Column(String(20), nullable=False)
    sesion = Column(String(64), nullable=False)        # sha256 del token: otra sesion no puede confirmarla
    conversacion_id = Column(String(32), nullable=True, index=True)
    accion = Column(String(40), nullable=False)
    objetivo = Column(JSON, nullable=False)            # {pedido_id, codigo, ruta_id...}
    titulo = Column(String(120), nullable=False)
    detalle = Column(Text, nullable=False, default="")
    estado = Column(String(12), nullable=False, default=PENDIENTE, index=True)
    creada_en = Column(DateTime, default=ahora_utc, nullable=False)
    vence_en = Column(DateTime, nullable=False)
    resuelta_en = Column(DateTime, nullable=True)
    resultado = Column(Text, nullable=True)            # mensaje del nucleo o motivo del error


class AuditoriaAccion(Base):
    """Cada paso de una accion: propuesta, confirmada, cancelada, vencida, rechazada, ejecutada o error,
    con el usuario que lo hizo (el que confirmo, en el caso de la ejecucion)."""

    __tablename__ = "auditoria_acciones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    creado_en = Column(DateTime, default=ahora_utc, nullable=False, index=True)
    propuesta_id = Column(String(32), nullable=True, index=True)
    evento = Column(String(12), nullable=False)
    accion = Column(String(40), nullable=True)
    usuario_id = Column(Integer, nullable=False, index=True)
    usuario_correo = Column(String(120), nullable=False)
    rol = Column(String(20), nullable=False)
    detalle = Column(Text, nullable=True)
