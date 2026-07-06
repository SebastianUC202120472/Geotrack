from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float
from app.db.database import Base


class Reclamo(Base):
    """Registro del Libro de Reclamaciones (Ley 29571)."""

    __tablename__ = "reclamos"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), unique=True, index=True, nullable=True)  # LR-2026-XXXX
    tipo = Column(String(10), nullable=False)             # RECLAMO | QUEJA
    consumidor_nombre = Column(String(150), nullable=False)
    consumidor_dni = Column(String(20), nullable=True)
    consumidor_domicilio = Column(String(255), nullable=True)
    consumidor_email = Column(String(150), nullable=True)
    consumidor_telefono = Column(String(30), nullable=True)
    es_menor = Column(Boolean, default=False)
    bien_tipo = Column(String(12), nullable=True)         # PRODUCTO | SERVICIO
    bien_descripcion = Column(Text, nullable=True)
    monto_reclamado = Column(Float, nullable=True)
    detalle = Column(Text, nullable=False)
    pedido_codigo = Column(String(20), nullable=True)
    creado_en = Column(DateTime, default=datetime.utcnow)
