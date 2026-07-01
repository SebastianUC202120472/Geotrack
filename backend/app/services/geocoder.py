import os
import time

from geopy.geocoders import Nominatim, GoogleV3
from geopy.exc import GeocoderTimedOut

_GOOGLE_KEY = os.getenv("GOOGLE_GEOCODING_KEY", "").strip()

_nominatim = Nominatim(user_agent="siol_sava_tesis_geocoder")
_google = GoogleV3(api_key=_GOOGLE_KEY) if _GOOGLE_KEY else None


def usando_google() -> bool:
    """Devuelve True si hay key de Google configurada."""
    return _google is not None


def obtener_coordenadas(direccion: str, db=None, forzar: bool = False):
    """Geocodifica una direccion y devuelve (lat, lng) o (None, None). Recibe: texto de direccion, db opcional para cache, forzar para ignorar cache."""
    direccion = (direccion or "").strip()
    if not direccion:
        return None, None

    cache_repo = None
    if db is not None:
        from app.repositories import geocoding_cache_repository as cache_repo
        if not forzar:
            cacheada = cache_repo.obtener(db, direccion)
            if cacheada is not None:
                return cacheada.latitud, cacheada.longitud

    try:
        if _google is not None:
            location = _google.geocode(direccion, region="pe", timeout=10)
        else:
            # Nominatim limita a 1 req/s para evitar bloqueo de IP.
            time.sleep(1)
            location = _nominatim.geocode(direccion, timeout=10)

        if location:
            if cache_repo is not None:
                cache_repo.guardar(db, direccion, location.latitude, location.longitude,
                                   "google" if _google is not None else "nominatim")
            return location.latitude, location.longitude
        return None, None
    except GeocoderTimedOut:
        return None, None
    except Exception as e:
        print(f"Error geocodificando {direccion}: {e}")
        return None, None
