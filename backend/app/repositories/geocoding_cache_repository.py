# app/repositories/geocoding_cache_repository.py
# Única capa que lee/escribe la tabla 'geocodificaciones_cache' (caché de direcciones).
import re
from typing import Optional

from sqlalchemy.orm import Session

from app.models.geocoding_cache import GeocodificacionCache


def _normalizar(direccion: str) -> str:
    """Clave de caché: dirección en minúsculas y con los espacios colapsados, para que
    'Av. Larco 137 ' y 'av.  larco 137' apunten a la misma entrada. Recibe: la dirección."""
    return re.sub(r"\s+", " ", (direccion or "").strip().lower())


def obtener(db: Session, direccion: str) -> Optional[GeocodificacionCache]:
    """Devuelve la entrada cacheada de una dirección, o None si no está. Recibe: la dirección."""
    norm = _normalizar(direccion)
    if not norm:
        return None
    return (
        db.query(GeocodificacionCache)
        .filter(GeocodificacionCache.direccion_normalizada == norm)
        .first()
    )


def guardar(db: Session, direccion: str, latitud: float, longitud: float, proveedor: Optional[str]) -> None:
    """Inserta o actualiza la coordenada cacheada de una dirección. Hace flush (NO commit) para
    que una segunda búsqueda en la MISMA transacción ya la encuentre (la sesión usa autoflush=False).
    Recibe: la dirección, lat/lng y el proveedor que la resolvió."""
    norm = _normalizar(direccion)
    if not norm:
        return
    existente = obtener(db, direccion)
    if existente:
        existente.latitud = latitud
        existente.longitud = longitud
        existente.proveedor = proveedor
    else:
        db.add(GeocodificacionCache(
            direccion_normalizada=norm, latitud=latitud, longitud=longitud, proveedor=proveedor,
        ))
    db.flush()
