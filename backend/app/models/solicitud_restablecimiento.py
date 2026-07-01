from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.db.database import Base


class SolicitudRestablecimiento(Base):
    """Solicitud de restablecimiento de contraseña de un conductor. Estados: PENDIENTE -> ATENDIDA."""
    __tablename__ = "solicitudes_restablecimiento"

    id = Column(Integer, primary_key=True, index=True)
    conductor_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    correo = Column(String(120), nullable=False)        # correo con el que se solicitó (snapshot)
    estado = Column(String(20), default="PENDIENTE")     # PENDIENTE -> ATENDIDA
    fecha_solicitud = Column(DateTime, default=datetime.utcnow)
    fecha_atencion = Column(DateTime, nullable=True)     # cuándo el admin la atendió
