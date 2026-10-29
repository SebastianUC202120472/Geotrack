# Almacenamiento de archivos subidos (fotos, guias, liquidaciones) (EX-08).
# - "local" (por defecto): carpeta UPLOADS_DIR; docker-compose la monta en un volumen y sobrevive a los rebuilds.
# - "supabase": Supabase Storage (bucket privado); sobrevive a cambiar de servidor. Si un archivo no esta en la
#   nube se busca en el disco local, asi las fotos guardadas antes del cambio siguen visibles.
# Las claves son rutas relativas como "evidencias/pod_1_2_ab.jpg"; en la BD se guardan como "/media/<clave>".
import mimetypes
import os
import urllib.error
import urllib.parse
import urllib.request

from app.core.config import settings
from app.core.registro import obtener_logger

PREFIJO_URL = "/media/"
CARPETA_PRIVADA = "privado/"  # nunca se sirve por /media (p. ej. liquidaciones)
_log = obtener_logger("almacenamiento")


def _validar_clave(clave: str) -> str:
    """Normaliza la clave y rechaza rutas absolutas o con '..'. Recibe la clave."""
    clave = (clave or "").replace("\\", "/").lstrip("/")
    partes = clave.split("/")
    if not clave or any(p in ("", ".", "..") for p in partes):
        raise ValueError("Clave de archivo inválida")
    return clave


def _ruta_local(clave: str) -> str:
    """Ruta en disco de una clave, siempre dentro de UPLOADS_DIR. Recibe la clave."""
    base = os.path.realpath(settings.UPLOADS_DIR)
    ruta = os.path.realpath(os.path.join(base, _validar_clave(clave)))
    if not ruta.startswith(base + os.sep):
        raise ValueError("Clave de archivo inválida")
    return ruta


def usa_nube() -> bool:
    """True si los archivos se guardan en Supabase Storage (configurado en el .env)."""
    return (settings.ALMACENAMIENTO or "").lower() == "supabase" and bool(
        settings.SUPABASE_URL.strip() and settings.SUPABASE_SERVICE_KEY.strip() and settings.SUPABASE_BUCKET.strip())


def _url_nube(clave: str) -> str:
    """URL del objeto en la API de Supabase Storage. Recibe la clave."""
    base = settings.SUPABASE_URL.rstrip("/")
    return f"{base}/storage/v1/object/{settings.SUPABASE_BUCKET}/{urllib.parse.quote(_validar_clave(clave))}"


def _pedir_nube(metodo: str, clave: str, contenido: bytes | None = None, tipo: str | None = None):
    """Hace la peticion a Supabase Storage con la clave de servicio. Devuelve los bytes o None si no existe."""
    cabeceras = {"Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}", "apikey": settings.SUPABASE_SERVICE_KEY}
    if contenido is not None:
        cabeceras.update({"Content-Type": tipo or "application/octet-stream", "x-upsert": "true"})
    peticion = urllib.request.Request(_url_nube(clave), data=contenido, method=metodo, headers=cabeceras)
    try:
        with urllib.request.urlopen(peticion, timeout=30) as resp:  # nosec B310 - URL del .env (https)
            return resp.read()
    except urllib.error.HTTPError as e:
        if e.code in (400, 404) and metodo in ("GET", "DELETE"):
            return None
        raise


def guardar(clave: str, contenido: bytes) -> str:
    """Guarda un archivo y devuelve su URL publica-firmable ("/media/<clave>"). Recibe la clave y los bytes."""
    clave = _validar_clave(clave)
    if usa_nube():
        tipo = mimetypes.guess_type(clave)[0] or "application/octet-stream"
        _pedir_nube("POST", clave, contenido, tipo)
    else:
        ruta = _ruta_local(clave)
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        with open(ruta, "wb") as f:
            f.write(contenido)
    return PREFIJO_URL + clave


def leer(clave: str) -> bytes | None:
    """Bytes del archivo o None si no existe (en la nube y, de respaldo, en el disco). Recibe la clave."""
    clave = _validar_clave(clave)
    if usa_nube():
        try:
            datos = _pedir_nube("GET", clave)
            if datos is not None:
                return datos
        except Exception:
            _log.exception("No se pudo leer %s de Supabase Storage", clave)
    ruta = _ruta_local(clave)
    if os.path.isfile(ruta):
        with open(ruta, "rb") as f:
            return f.read()
    return None


def existe(clave: str) -> bool:
    """True si el archivo existe. Recibe la clave."""
    try:
        return leer(clave) is not None
    except ValueError:
        return False


def borrar(clave: str) -> None:
    """Borra el archivo si existe (nube y disco). Recibe la clave."""
    clave = _validar_clave(clave)
    if usa_nube():
        try:
            _pedir_nube("DELETE", clave)
        except Exception:
            _log.exception("No se pudo borrar %s de Supabase Storage", clave)
    ruta = _ruta_local(clave)
    if os.path.isfile(ruta):
        os.remove(ruta)


def clave_de_url(url: str) -> str | None:
    """Clave de un archivo a partir de su URL "/media/..." (sin parametros). Recibe la URL."""
    if not url or not url.startswith(PREFIJO_URL):
        return None
    return url[len(PREFIJO_URL):].split("?", 1)[0]
