from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from app.db.database import Base


class Vehiculo(Base):
    __tablename__ = "vehiculos"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), unique=True, index=True, nullable=True)  # legible: VE-001
    placa = Column(String(20), unique=True, index=True, nullable=False)
    marca = Column(String(60), nullable=True)
    capacidad_volumetrica = Column(Float, nullable=True)  # m3 que puede cargar
    capacidad_cajas = Column(Integer, nullable=True)      # cuántas cajas soporta
    estado = Column(String(30), default="DISPONIBLE")     # DISPONIBLE, EN_RUTA, INACTIVO
    conductor_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True, index=True)  # NULL = vehículo de la empresa
    creado_en = Column(DateTime, default=datetime.utcnow)
    eliminado_en = Column(DateTime, nullable=True)  # borrado lógico
