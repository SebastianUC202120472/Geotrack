from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime

from app.db.database import Base


class GeocodificacionCache(Base):
    """Dirección normalizada y su coordenada cacheada para evitar llamadas repetidas al proveedor."""
    __tablename__ = "geocodificaciones_cache"

    id = Column(Integer, primary_key=True, index=True)
    # Dirección en minúsculas con espacios colapsados, usada como clave de búsqueda.
    direccion_normalizada = Column(String(500), unique=True, index=True, nullable=False)
    latitud = Column(Float, nullable=False)
    longitud = Column(Float, nullable=False)
    proveedor = Column(String(20), nullable=True)   # 'google' | 'nominatim'
    creado_en = Column(DateTime, default=datetime.utcnow)
