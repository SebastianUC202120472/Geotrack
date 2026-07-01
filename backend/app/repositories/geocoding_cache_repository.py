import re
from typing import Optional

from sqlalchemy.orm import Session

from app.models.geocoding_cache import GeocodificacionCache


def _normalizar(direccion: str) -> str:
    """Normaliza una dirección a minúsculas y sin espacios extra. Recibe: la dirección."""
    return re.sub(r"\s+", " ", (direccion or "").strip().lower())


def obtener(db: Session, direccion: str) -> Optional[GeocodificacionCache]:
    """Devuelve la entrada cacheada de una dirección o None. Recibe: sesión y dirección."""
    norm = _normalizar(direccion)
    if not norm:
        return None
    return (
        db.query(GeocodificacionCache)
        .filter(GeocodificacionCache.direccion_normalizada == norm)
        .first()
    )


def guardar(db: Session, direccion: str, latitud: float, longitud: float, proveedor: Optional[str]) -> None:
    """Inserta o actualiza la coordenada cacheada y hace flush. Recibe: sesión, dirección, lat/lng y proveedor."""
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
