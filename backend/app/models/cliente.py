from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float
from app.db.database import Base


class ClienteCorporativo(Base):
    __tablename__ = "clientes_corporativos"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), unique=True, index=True, nullable=True)  # ej: CL-001
    razon_social = Column(String(150), nullable=False)
    identificador_unico = Column(String(20), unique=True, index=True, nullable=True)  # RUC
    contacto = Column(String(100), nullable=True)
    direccion_origen = Column(String(255), nullable=True)         # punto de recojo del cliente
    distrito = Column(String(100), nullable=True)                 # se rellena al geocodificar
    latitud = Column(Float, nullable=True)
    longitud = Column(Float, nullable=True)
    creado_en = Column(DateTime, default=datetime.utcnow)
    eliminado_en = Column(DateTime, nullable=True)                # soft delete
