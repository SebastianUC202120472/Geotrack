import os
import time
from dataclasses import dataclass

from geopy.geocoders import Nominatim, GoogleV3

from app.core.distritos import elegir_distrito, normalizar_distrito, GENERICOS
from app.core.registro import obtener_logger

_GOOGLE_KEY = os.getenv("GOOGLE_GEOCODING_KEY", "").strip()

_nominatim = Nominatim(user_agent="siol_sava_tesis_geocoder")
_google = GoogleV3(api_key=_GOOGLE_KEY) if _GOOGLE_KEY else None

_log = obtener_logger("geocoder")

# Partes del resultado de Google que nombran al distrito (en Lima, "locality" es el distrito).
_TIPOS_GOOGLE = ("locality", "administrative_area_level_3", "sublocality_level_1", "sublocality", "neighborhood")
# Partes del resultado de OpenStreetMap que nombran al distrito ("city" suele ser la provincia).
_CLAVES_OSM = ("city_district", "suburb", "borough", "town", "village", "municipality")
# Resultados que solo ubican el pais, la region o un codigo postal: no sirven para entregar,
# cuentan como "no encontrado".
_GRUESOS_GOOGLE = {"country", "administrative_area_level_1", "administrative_area_level_2", "postal_code"}
_GRUESOS_OSM = {"country", "state", "region", "province", "county", "postcode"}


@dataclass
class ResultadoGeo:
    """Punto encontrado por el geocodificador con el distrito que trae el mapa (o None)."""
    latitud: float
    longitud: float
    distrito: str | None = None
    direccion: str | None = None
    proveedor: str | None = None


def usando_google() -> bool:
    """Devuelve True si hay key de Google configurada."""
    return _google is not None


def _distrito_google(raw: dict) -> str | None:
    """Saca el distrito de los componentes de un resultado de Google. Recibe el JSON del resultado."""
    componentes = raw.get("address_components") or []
    candidatos = [
        c.get("long_name") for tipo in _TIPOS_GOOGLE for c in componentes if tipo in (c.get("types") or [])
    ]
    return elegir_distrito(candidatos)


def _distrito_osm(raw: dict) -> str | None:
    """Saca el distrito del detalle de direccion de OpenStreetMap. Recibe el JSON del resultado."""
    direccion = raw.get("address") or {}
    candidatos = [direccion.get(k) for k in _CLAVES_OSM]
    # "city" solo sirve si nombra un distrito concreto (p. ej. Ventanilla), no "Lima".
    ciudad = normalizar_distrito(direccion.get("city"))
    if ciudad and ciudad not in GENERICOS:
        candidatos.append(ciudad)
    return elegir_distrito(candidatos)


def _desde_google(location) -> ResultadoGeo:
    """Convierte un resultado de geopy (Google) en ResultadoGeo. Recibe el Location."""
    return ResultadoGeo(location.latitude, location.longitude, _distrito_google(location.raw or {}),
                        location.address, "google")


def _desde_osm(location) -> ResultadoGeo:
    """Convierte un resultado de geopy (Nominatim) en ResultadoGeo. Recibe el Location."""
    return ResultadoGeo(location.latitude, location.longitude, _distrito_osm(location.raw or {}),
                        location.address, "nominatim")


def _buscar_google(texto: str, maximo: int) -> list[ResultadoGeo]:
    """Consulta a Google (solo Peru). Recibe el texto y el maximo de resultados. Lanza si Google falla."""
    encontrados = _google.geocode(texto, exactly_one=False, region="pe", components={"country": "PE"}, timeout=10)
    utiles = [loc for loc in encontrados or [] if not _GRUESOS_GOOGLE & set((loc.raw or {}).get("types") or [])]
    return [_desde_google(loc) for loc in utiles[:maximo]]


def _buscar_osm(texto: str, maximo: int) -> list[ResultadoGeo]:
    """Consulta a OpenStreetMap (solo Peru), respetando su limite de 1 consulta por segundo.
    Recibe el texto y el maximo de resultados. Lanza si el servicio falla."""
    time.sleep(1)
    encontrados = _nominatim.geocode(texto, exactly_one=False, limit=maximo, addressdetails=True,
                                     country_codes="pe", timeout=10)
    utiles = [loc for loc in encontrados or [] if (loc.raw or {}).get("addresstype") not in _GRUESOS_OSM]
    return [_desde_osm(loc) for loc in utiles[:maximo]]


def buscar_coincidencias(texto: str, maximo: int = 1) -> list[ResultadoGeo]:
    """Geocodifica un texto con Google y, si Google falla o no encuentra nada, con OpenStreetMap
    (C16-02). Recibe el texto y el maximo de coincidencias; devuelve la lista (vacia si no hay)."""
    texto = (texto or "").strip()
    if not texto:
        return []
    if _google is not None:
        try:
            resultados = _buscar_google(texto, maximo)
            if resultados:
                return resultados
        except Exception as e:  # cuota agotada, clave revocada, red caida...
            _log.warning("Google no pudo geocodificar '%s' (%s); se intenta con OpenStreetMap", texto, e)
    try:
        return _buscar_osm(texto, maximo)
    except Exception as e:
        _log.warning("OpenStreetMap no pudo geocodificar '%s': %s", texto, e)
        return []


def _cerca(a: ResultadoGeo, b: ResultadoGeo) -> bool:
    """True si dos resultados caen a menos de ~150 m (son el mismo lugar). Recibe dos ResultadoGeo."""
    return abs(a.latitud - b.latitud) < 0.0015 and abs(a.longitud - b.longitud) < 0.0015


def buscar_lugares(texto: str, maximo: int = 5) -> list[ResultadoGeo]:
    """Lugares posibles para la busqueda manual del admin (C17-02): Google suele dar uno solo, asi
    que se suman los de OpenStreetMap sin repetir lugares cercanos. Recibe el texto y el maximo."""
    lugares = buscar_coincidencias(texto, maximo)
    if _google is None or not lugares or lugares[0].proveedor != "google":
        return lugares  # ya vienen de OpenStreetMap (o no hay nada)
    try:
        extra = _buscar_osm(texto, maximo)
    except Exception as e:
        _log.warning("OpenStreetMap no pudo completar la busqueda '%s': %s", texto.strip(), e)
        extra = []
    for lugar in extra:
        if len(lugares) >= maximo:
            break
        if not any(_cerca(lugar, otro) for otro in lugares):
            lugares.append(lugar)
    return lugares


def geocodificar(direccion: str, db=None, forzar: bool = False) -> ResultadoGeo | None:
    """Geocodifica una direccion usando el cache de direcciones si hay sesion. Recibe el texto, la
    sesion db opcional y forzar para ignorar el cache. Devuelve ResultadoGeo o None si no se ubica."""
    direccion = (direccion or "").strip()
    if not direccion:
        return None

    cache_repo = None
    if db is not None:
        from app.repositories import geocoding_cache_repository as cache_repo
        if not forzar:
            cacheada = cache_repo.obtener(db, direccion)
            # Las entradas antiguas no guardaban el distrito: esas se vuelven a consultar una vez.
            if cacheada is not None and cacheada.distrito:
                return ResultadoGeo(cacheada.latitud, cacheada.longitud, cacheada.distrito,
                                    None, cacheada.proveedor)

    resultados = buscar_coincidencias(direccion)
    if not resultados:
        return None
    mejor = resultados[0]
    if cache_repo is not None:
        cache_repo.guardar(db, direccion, mejor.latitud, mejor.longitud, mejor.proveedor, mejor.distrito)
    return mejor


def obtener_coordenadas(direccion: str, db=None, forzar: bool = False):
    """Geocodifica una direccion y devuelve (lat, lng) o (None, None). Recibe: texto de direccion, db opcional para cache, forzar para ignorar cache."""
    resultado = geocodificar(direccion, db, forzar)
    if resultado is None:
        return None, None
    return resultado.latitud, resultado.longitud


def distrito_de_punto(latitud: float, longitud: float) -> str | None:
    """Distrito de un punto marcado a mano en el mapa (geocodificacion inversa, Google y luego
    OpenStreetMap). Recibe latitud y longitud; devuelve el nombre oficial o None."""
    if _google is not None:
        try:
            for loc in _google.reverse((latitud, longitud), exactly_one=False, timeout=10) or []:
                distrito = _distrito_google(loc.raw or {})
                if distrito:
                    return distrito
        except Exception as e:
            _log.warning("Google no pudo ubicar el punto %s,%s (%s); se intenta con OpenStreetMap", latitud, longitud, e)
    try:
        time.sleep(1)
        loc = _nominatim.reverse((latitud, longitud), zoom=14, addressdetails=True, timeout=10)
        return _distrito_osm(loc.raw or {}) if loc else None
    except Exception as e:
        _log.warning("OpenStreetMap no pudo ubicar el punto %s,%s: %s", latitud, longitud, e)
        return None
