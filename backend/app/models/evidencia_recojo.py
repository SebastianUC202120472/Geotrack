# app/models/evidencia_recojo.py
# Define la tabla 'evidencias_recojo': las fotos (boleta/guía/bultos) que el conductor
# sube al registrar la recepción de un recojo. Relación 1:N con solicitudes_recojo
# (antes solo se guardaba una foto en solicitud_recojo.url_guia).
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.db.database import Base


class EvidenciaRecojo(Base):
    __tablename__ = "evidencias_recojo"

    id = Column(Integer, primary_key=True, index=True)
    recojo_id = Column(Integer, ForeignKey("solicitudes_recojo.id"), index=True, nullable=False)
    url_foto = Column(String(255), nullable=False)   # /media/guias/guia_<ruta>_<recojo>_<i>.<ext>
    secuencia = Column(Integer, default=0)            # orden de captura (0,1,2,…)
    creado_en = Column(DateTime, default=datetime.utcnow)
