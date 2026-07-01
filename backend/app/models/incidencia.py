from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean, ForeignKey
from app.db.database import Base


class Incidencia(Base):
    """Auxilio mecanico reportado por el conductor; mientras esta ABIERTA la ruta queda PAUSADA."""

    __tablename__ = "incidencias"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), unique=True, index=True, nullable=True)  # legible: IN-001
    ruta_id = Column(Integer, ForeignKey("rutas.id"), nullable=False, index=True)
    conductor_id = Column(Integer, nullable=False, index=True)
    vehiculo_placa = Column(String(20), nullable=True)
    tipo = Column(String(40), default="AVERIA_MECANICA")
    descripcion = Column(Text, nullable=True)
    url_evidencia = Column(String(255), nullable=True)
    latitud = Column(Float, nullable=True)
    longitud = Column(Float, nullable=True)
    estado = Column(String(20), default="ABIERTA")  # ABIERTA | RESUELTA
    creado_en = Column(DateTime, default=datetime.utcnow, index=True)
    resuelto_en = Column(DateTime, nullable=True)
    resuelto_por = Column(Integer, nullable=True)  # solo el conductor puede reanudar
    nota_resolucion = Column(String(255), nullable=True)
    puede_solucionar_solo = Column(Boolean, default=False)  # el conductor indica si puede resolverla solo
    ayuda_enviada_en = Column(DateTime, nullable=True)
    ayuda_enviada_por = Column(Integer, nullable=True)  # admin que mando la ayuda
    ayuda_detalle = Column(String(255), nullable=True)
