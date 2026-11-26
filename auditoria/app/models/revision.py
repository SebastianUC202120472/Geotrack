from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.database import Base


class RevisionHumana(Base):
    """Registro inmutable de auditoría para decisiones tomadas por un administrador."""

    __tablename__ = "revisiones_humanas"

    id = Column(Integer, primary_key=True, index=True)
    analisis_id = Column(Integer, ForeignKey("analisis_evidencias.id"), nullable=False, index=True)

    admin_id = Column(Integer, nullable=False)             # ID del usuario administrador en public.usuarios
    admin_email = Column(String(100), nullable=False)      # Correo del admin que resolvió
    dictamen = Column(String(20), nullable=False)          # 'VALIDA' o 'OBSERVADA'
    motivo = Column(Text, nullable=True)                   # Justificación u observaciones del administrador

    registrado_en = Column(DateTime, default=datetime.utcnow, index=True)

    analisis = relationship("EvidenciaAnalisis", back_populates="revisiones")
