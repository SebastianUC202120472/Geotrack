from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime

from app.db.database import Base


class ColaTrabajo(Base):
    """Cola de evidencias pendientes de análisis en segundo plano con control de reintentos."""

    __tablename__ = "cola_trabajo"

    id = Column(Integer, primary_key=True, index=True)
    evidencia_id = Column(Integer, nullable=False, unique=True, index=True)
    pedido_id = Column(Integer, nullable=False, index=True)
    url_foto = Column(String(255), nullable=False)

    # PENDIENTE, PROCESANDO, COMPLETADO, FALLIDO, OMITIDO_TOPE
    estado = Column(String(20), nullable=False, default="PENDIENTE", index=True)
    intentos = Column(Integer, nullable=False, default=0)
    ultimo_error = Column(Text, nullable=True)

    programado_para = Column(DateTime, default=datetime.utcnow, index=True)
    creado_en = Column(DateTime, default=datetime.utcnow)
    actualizado_en = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
