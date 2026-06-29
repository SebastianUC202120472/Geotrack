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


def obtener_coordenadas(direccion: str):
    """
    Devuelve una tupla (latitud, longitud) para una dirección, o (None, None) si no se
    encuentra o hay error. Con GOOGLE_GEOCODING_KEY usa Google (preciso, por número de
    puerta); si no, Nominatim/OSM. Recibe: la dirección en texto.
    """
    direccion = (direccion or "").strip()
    if not direccion:
        return None, None
    try:
        if _google is not None:
            # Google: preciso y sin límite de 1/s; 'region=pe' sesga los resultados a Perú.
            location = _google.geocode(direccion, region="pe")
        else:
            # Nominatim es gratuito pero limita a 1 petición por segundo (evita bloqueo de IP).
            time.sleep(1)
            location = _nominatim.geocode(direccion)

        if location:
            return location.latitude, location.longitude
        return None, None
    except GeocoderTimedOut:
        # El servidor tardó demasiado en responder.
        return None, None
    except Exception as e:
        # Cualquier otro error: lo registramos y seguimos sin romper la carga.
        print(f"Error geocodificando {direccion}: {e}")
        return None, None
