# app/models/solicitud_restablecimiento.py
# Tabla 'solicitudes_restablecimiento' (extra del CUS-04): cuando un conductor olvida
# su contraseña, pide desde el Login que se la restablezcan. La solicitud queda
# PENDIENTE hasta que el admin le fija una clave nueva (entonces pasa a ATENDIDA).
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.db.database import Base


class SolicitudRestablecimiento(Base):
    __tablename__ = "solicitudes_restablecimiento"

    id = Column(Integer, primary_key=True, index=True)
    conductor_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    correo = Column(String(120), nullable=False)        # correo con el que se solicitó (snapshot)
    estado = Column(String(20), default="PENDIENTE")     # PENDIENTE -> ATENDIDA
    fecha_solicitud = Column(DateTime, default=datetime.utcnow)
    fecha_atencion = Column(DateTime, nullable=True)     # cuándo el admin la atendió
