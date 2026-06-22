# app/models/paquete_esperado.py
# Tablas del módulo de almacén (CUS-14): la trama de paquetes esperados de un recojo
# y los escaneos que no estaban en la trama (sobrantes/desconocidos).
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.db.database import Base


class PaqueteEsperado(Base):
    """Un código de rastreo que se espera recibir dentro de un recojo (la 'trama')."""
    __tablename__ = "paquetes_esperados"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(50), index=True, nullable=False)   # tracking esperado (lo que se escanea)
    recojo_id = Column(Integer, ForeignKey("solicitudes_recojo.id"), nullable=False, index=True)
    estado = Column(String(20), default="ESPERADO")           # ESPERADO -> INGRESADO
    escaneado_en = Column(DateTime, nullable=True)            # sello al escanear
    escaneado_por = Column(Integer, nullable=True)            # id del usuario de almacén
    creado_en = Column(DateTime, default=datetime.utcnow)     # al importar la trama


class EscaneoDesconocido(Base):
    """Un código escaneado que NO estaba en la trama del recojo (sobrante)."""
    __tablename__ = "escaneos_desconocidos"

    id = Column(Integer, primary_key=True, index=True)
    recojo_id = Column(Integer, ForeignKey("solicitudes_recojo.id"), nullable=False, index=True)
    codigo = Column(String(50), nullable=False)
    escaneado_en = Column(DateTime, default=datetime.utcnow)
    escaneado_por = Column(Integer, nullable=True)
