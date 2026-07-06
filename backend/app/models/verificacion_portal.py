from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from app.db.database import Base


class VerificacionPortal(Base):
    """Reto de verificacion del portal: OTP + control de intentos/bloqueo + auditoria."""

    __tablename__ = "verificaciones_portal"

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String(10), nullable=False)            # PERSONA | EMPRESA
    referencia = Column(String(40), index=True, nullable=False)  # codigo pedido o codigo_acceso
    canal = Column(String(12), nullable=True)            # DNI | OTP_CORREO
    codigo_hash = Column(String(255), nullable=True)     # hash del OTP vigente
    expira_en = Column(DateTime, nullable=True)
    intentos = Column(Integer, default=0)
    bloqueado_hasta = Column(DateTime, nullable=True)
    creado_en = Column(DateTime, default=datetime.utcnow)
    verificado_en = Column(DateTime, nullable=True)
