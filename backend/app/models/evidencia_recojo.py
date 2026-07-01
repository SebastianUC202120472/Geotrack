from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.db.database import Base


class EvidenciaRecojo(Base):
    """Fotos subidas por el conductor al registrar un recojo. Relacion N:1 con solicitudes_recojo."""
    __tablename__ = "evidencias_recojo"

    id = Column(Integer, primary_key=True, index=True)
    recojo_id = Column(Integer, ForeignKey("solicitudes_recojo.id"), index=True, nullable=False)
    url_foto = Column(String(255), nullable=False)   # /media/guias/guia_<ruta>_<recojo>_<i>.<ext>
    secuencia = Column(Integer, default=0)            # orden de captura (0,1,2,…)
    creado_en = Column(DateTime, default=datetime.utcnow)
