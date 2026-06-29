# app/models/geocoding_cache.py
# Caché de geocodificación: guarda la coordenada de cada dirección ya resuelta para no
# volver a llamar al proveedor (Google) por la misma dirección. Ahorra cuota y costo cuando
# se reenvía el mismo Excel, hay direcciones repetidas o se re-geocodifica.
from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime

from app.db.database import Base


class GeocodificacionCache(Base):
    """Una dirección (normalizada) y su coordenada, cacheada para reutilizarla."""
    __tablename__ = "geocodificaciones_cache"

    id = Column(Integer, primary_key=True, index=True)
    # Clave de búsqueda: la dirección en minúsculas y con espacios colapsados (ver repositorio).
    direccion_normalizada = Column(String(500), unique=True, index=True, nullable=False)
    latitud = Column(Float, nullable=False)
    longitud = Column(Float, nullable=False)
    proveedor = Column(String(20), nullable=True)   # 'google' | 'nominatim'
    creado_en = Column(DateTime, default=datetime.utcnow)
