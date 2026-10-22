from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.base import Base  # O la clase Base que use tu proyecto

class VinculacionPlacaModel(Base):
    __tablename__ = "vinculaciones_placa"

    id = Column(Integer, primary_key=True, index=True)
    placa = Column(String(10), unique=True, nullable=False, index=True)
    modelo_id = Column(String(50), nullable=False)
    creado_por = Column(String(100), nullable=False)  # Guarda el email o ID del usuario
    creado_en = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())