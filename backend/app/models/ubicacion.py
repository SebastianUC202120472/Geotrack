from datetime import datetime
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from app.db.database import Base


class UbicacionConductor(Base):
    """Ultima posicion conocida de cada conductor (una fila por conductor, se sobreescribe)."""

    __tablename__ = "ubicaciones_conductor"

    id = Column(Integer, primary_key=True, index=True)
    conductor_id = Column(Integer, ForeignKey("usuarios.id"), unique=True, index=True, nullable=False)
    latitud = Column(Float, nullable=False)
    longitud = Column(Float, nullable=False)
    actualizado_en = Column(DateTime, default=datetime.utcnow)
