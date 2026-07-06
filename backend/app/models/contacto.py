from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from app.db.database import Base


class ContactoComercial(Base):
    """Lead del formulario de contacto del landing."""

    __tablename__ = "contactos_comerciales"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(120), nullable=False)
    empresa = Column(String(120), nullable=True)
    email = Column(String(150), nullable=False)
    telefono = Column(String(30), nullable=True)
    volumen_estimado = Column(Integer, nullable=True)
    mensaje = Column(Text, nullable=True)
    creado_en = Column(DateTime, default=datetime.utcnow)
