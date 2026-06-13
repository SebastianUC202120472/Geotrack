# app/models/vehiculo.py
# ============================================================================
# CAPA: MODELO (tabla de base de datos) — Clean Architecture
# ----------------------------------------------------------------------------
# ¿QUÉ HACE?  Define la tabla 'vehiculos': la flota que realiza las entregas.
#             Un vehículo puede ser del propio conductor o de la empresa.
# ¿CON QUÉ SE CONECTA?
#   - Hereda de 'Base' (db/database.py).
#   - 'conductor_id' -> usuarios.id (dueño/asignado). Si es NULL = de la empresa.
#   - La consultan: repositories/vehiculo_repository.py y vehiculo_service.py.
# ============================================================================
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
    estado = Column(String(30), default="DISPONIBLE")     # DISPONIBLE, EN_RUTA, INACTIVO
    # Dueño/asignado: el conductor (usuario). NULL = vehículo de la empresa.
    conductor_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True, index=True)
    creado_en = Column(DateTime, default=datetime.utcnow)
    eliminado_en = Column(DateTime, nullable=True)  # borrado lógico
