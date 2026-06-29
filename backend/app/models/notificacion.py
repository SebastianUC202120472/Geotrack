# app/models/notificacion.py
# Modelo de la tabla `notificaciones` para el historial de avisos del panel admin.
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime

from app.db.database import Base


class Notificacion(Base):
    """Registro de un aviso generado para el admin (entrega, incidencia, recojo, etc.)."""
    __tablename__ = "notificaciones"

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String(30), nullable=False)        # reportes|incidencias|recojos|correos|restablecimientos
    titulo = Column(String(120), nullable=False)
    mensaje = Column(String(255), nullable=True)
    ruta = Column(String(120), nullable=True)        # a dónde navega el panel
    entidad_id = Column(Integer, nullable=True)      # id de la entidad relacionada
    creado_en = Column(DateTime, default=datetime.utcnow, index=True)
    visto_en = Column(DateTime, nullable=True)       # null = no vista
