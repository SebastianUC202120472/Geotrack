from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from app.db.database import Base


class Usuario(Base):
    """Modelo de usuario del sistema (admin o conductor)."""

    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), unique=True, index=True, nullable=True)  # ej. AD-001 / CO-001
    correo = Column(String(100), unique=True, index=True, nullable=False)
    hash_contrasena = Column(String(255), nullable=False)
    rol = Column(String(20), nullable=False)  # 'admin' o 'conductor'
    estado = Column(Boolean, default=True)  # False = deshabilitado
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    nombre = Column(String(120), nullable=True)
    dni = Column(String(15), nullable=True)
    telefono = Column(String(20), nullable=True)
    cargo = Column(String(80), nullable=True)
