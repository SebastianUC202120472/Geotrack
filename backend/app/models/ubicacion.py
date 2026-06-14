# app/models/ubicacion.py
# Última posición conocida de cada conductor (para el mapa de flota en vivo).
from datetime import datetime
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from app.db.database import Base


class UbicacionConductor(Base):
    __tablename__ = "ubicaciones_conductor"

    id = Column(Integer, primary_key=True, index=True)
    # Una fila por conductor: se va sobrescribiendo (última posición conocida).
    conductor_id = Column(Integer, ForeignKey("usuarios.id"), unique=True, index=True, nullable=False)
    latitud = Column(Float, nullable=False)
    longitud = Column(Float, nullable=False)
    actualizado_en = Column(DateTime, default=datetime.utcnow)  # cuándo llegó la última señal
