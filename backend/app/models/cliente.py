# app/models/cliente.py
# Define la tabla 'clientes_corporativos'.
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float
from app.db.database import Base


class ClienteCorporativo(Base):
    __tablename__ = "clientes_corporativos"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), unique=True, index=True, nullable=True)  # legible: CL-001
    razon_social = Column(String(150), nullable=False)            # nombre legal de la empresa
    identificador_unico = Column(String(20), unique=True, index=True, nullable=True)  # RUC (único)
    contacto = Column(String(100), nullable=True)                 # correo/teléfono de contacto
    direccion_origen = Column(String(255), nullable=True)         # punto de recojo (almacén/tienda del cliente)
    distrito = Column(String(100), nullable=True)                 # se rellena al geocodificar (CUS-16)
    latitud = Column(Float, nullable=True)                        # coordenada del punto de recojo (geocodificada)
    longitud = Column(Float, nullable=True)                       # coordenada del punto de recojo (geocodificada)
    creado_en = Column(DateTime, default=datetime.utcnow)
    eliminado_en = Column(DateTime, nullable=True)                # borrado lógico (soft delete)
