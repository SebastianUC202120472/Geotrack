from sqlalchemy import Column, Integer, String, ForeignKey
from app.db.database import Base


class PerfilConductor(Base):
    """Datos personales del conductor (nombre, teléfono, DNI). Vinculado a un usuario."""
    __tablename__ = "conductor_perfiles"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), unique=True, nullable=False, index=True)
    nombre = Column(String(120), nullable=False)
    telefono = Column(String(30), nullable=True)
    dni = Column(String(20), nullable=True)
    foto_url = Column(String(255), nullable=True)  # ruta /media/conductores/...; la sube el admin
