# app/services/geocoder.py
# Convierte una dirección en texto ("Av. Pardo 174, Miraflores, Lima") a coordenadas.
# Usa Google Geocoding (preciso) si hay GOOGLE_GEOCODING_KEY en el entorno; si no, cae a
# Nominatim/OSM (gratis, pero menos preciso y limitado a 1 req/s).
import os
import time

from geopy.geocoders import Nominatim, GoogleV3
from geopy.exc import GeocoderTimedOut

# La key de geocoding vive SOLO en el backend (nunca en la app móvil) por seguridad y cuota.
_GOOGLE_KEY = os.getenv("GOOGLE_GEOCODING_KEY", "").strip()

# Nominatim EXIGE un 'user_agent' propio; si no, bloquea las peticiones.
_nominatim = Nominatim(user_agent="siol_sava_tesis_geocoder")
# Google solo se inicializa si hay key (si no, queda en None y usamos Nominatim).
_google = GoogleV3(api_key=_GOOGLE_KEY) if _GOOGLE_KEY else None


def usando_google() -> bool:
    """True si hay key de Google y por tanto se geocodifica con precisión de Google."""
    return _google is not None


def obtener_coordenadas(direccion: str, db=None, forzar: bool = False):
    """
    Devuelve una tupla (latitud, longitud) para una dirección, o (None, None) si no se
    encuentra o hay error. Con GOOGLE_GEOCODING_KEY usa Google (preciso, por número de
    puerta); si no, Nominatim/OSM. Recibe: la dirección en texto.

    CACHÉ (opcional): si se pasa `db`, reutiliza coordenadas ya resueltas para no volver a
    llamar al proveedor por la misma dirección (ahorra cuota/costo al reenviar el mismo Excel
    o con direcciones repetidas). Solo se cachean ACIERTOS: una dirección no encontrada NO se
    cachea, para que se reintente luego. Con `forzar=True` ignora el caché y geocodifica de
    nuevo (lo usa "regeocodificar" para refrescar), pero igual actualiza el caché con el dato.
    """
    direccion = (direccion or "").strip()
    if not direccion:
        return None, None

    # Caché: import perezoso para no acoplar este módulo de bajo nivel al cargar.
    cache_repo = None
    if db is not None:
        from app.repositories import geocoding_cache_repository as cache_repo
        if not forzar:
            cacheada = cache_repo.obtener(db, direccion)
            if cacheada is not None:
                return cacheada.latitud, cacheada.longitud

    try:
        if _google is not None:
            # Google: preciso y sin límite de 1/s; 'region=pe' sesga los resultados a Perú.
            # timeout: si Google no responde en 10 s, abortamos (sin esto una respuesta colgada
            # bloquea el worker indefinidamente, sobre todo en geocodificación masiva de fondo).
            location = _google.geocode(direccion, region="pe", timeout=10)
        else:
            # Nominatim es gratuito pero limita a 1 petición por segundo (evita bloqueo de IP).
            time.sleep(1)
            location = _nominatim.geocode(direccion, timeout=10)

        if location:
            if cache_repo is not None:
                cache_repo.guardar(db, direccion, location.latitude, location.longitude,
                                   "google" if _google is not None else "nominatim")
            return location.latitude, location.longitude
        return None, None
    except GeocoderTimedOut:
        # El servidor tardó demasiado en responder.
        return None, None
    except Exception as e:
        # Cualquier otro error: lo registramos y seguimos sin romper la carga.
        print(f"Error geocodificando {direccion}: {e}")
        return None, None
