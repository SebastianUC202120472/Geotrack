# app/services/geocoder.py
# ============================================================================
# CAPA: SERVICIO (utilidad externa) — Inteligencia Geográfica (CUS-15)
# ----------------------------------------------------------------------------
# ¿QUÉ HACE?  Convierte una dirección en texto ("Av. X, San Miguel") en
#             coordenadas (latitud, longitud) usando el servicio Nominatim
#             de OpenStreetMap (gratuito) a través de la librería geopy.
# ¿CON QUÉ SE CONECTA?
#   - Lo USA: services/pedido_service.py durante la geocodificación.
# ============================================================================
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import time

# Nominatim EXIGE un 'user_agent' propio; si no, bloquea las peticiones.
geolocator = Nominatim(user_agent="siol_sava_tesis_geocoder")


def obtener_coordenadas(direccion: str):
    """
    Devuelve una tupla (latitud, longitud) para una dirección.
    Si no encuentra la dirección o hay un error, devuelve (None, None).
    """
    try:
        # Nominatim es gratuito pero limita a 1 petición por segundo.
        # Esta pausa evita que bloqueen nuestra IP.
        time.sleep(1)
        location = geolocator.geocode(direccion)

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
