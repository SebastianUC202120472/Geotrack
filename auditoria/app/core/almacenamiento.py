import os
import urllib.parse
import urllib.request
import urllib.error
from typing import Optional

from app.core.config import settings
from app.core.registro import obtener_logger

_log = obtener_logger("almacenamiento")
PREFIJO_URL = "/media/"
_demo_cache: dict[str, bytes] = {}


def guardar_demo_memoria(url_o_clave: str, contenido: bytes) -> None:
    """Guarda una imagen sintética de demostración en memoria sin escribir en el volumen :ro."""
    clave = clave_de_url(url_o_clave)
    if clave and contenido:
        _demo_cache[clave] = contenido


def clave_de_url(url: str) -> Optional[str]:
    """Obtiene la clave relativa de almacenamiento a partir de una URL '/media/...'.
    Ejemplo: '/media/evidencias/pod_1_2.jpg' -> 'evidencias/pod_1_2.jpg'
    """
    if not url:
        return None
    limpia = url.split("?", 1)[0].split("#", 1)[0]
    if limpia.startswith(PREFIJO_URL):
        return limpia[len(PREFIJO_URL):].lstrip("/")
    if limpia.startswith("/"):
        return limpia.lstrip("/")
    return limpia


def _validar_clave(clave: str) -> str:
    """Normaliza y rechaza intentos de path traversal."""
    clave = (clave or "").replace("\\", "/").strip("/")
    partes = clave.split("/")
    if not clave or any(p in ("", ".", "..") for p in partes):
        raise ValueError("Clave de archivo inválida o insegura")
    return clave


def _ruta_local(clave: str) -> str:
    """Resuelve la ruta absoluta en disco asegurando que esté dentro de UPLOADS_DIR."""
    base = os.path.realpath(settings.UPLOADS_DIR)
    clave_segura = _validar_clave(clave)
    ruta = os.path.realpath(os.path.join(base, clave_segura))
    if not ruta.startswith(base + os.sep) and ruta != base:
        raise ValueError("Intento de escape de directorio detectado")
    return ruta


def _leer_supabase(clave: str) -> Optional[bytes]:
    """Descarga el archivo desde Supabase Storage si está configurado."""
    if not (settings.SUPABASE_URL and settings.SUPABASE_SERVICE_KEY and settings.SUPABASE_BUCKET):
        return None
    base = settings.SUPABASE_URL.rstrip("/")
    url = f"{base}/storage/v1/object/{settings.SUPABASE_BUCKET}/{urllib.parse.quote(_validar_clave(clave))}"
    cabeceras = {
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
        "apikey": settings.SUPABASE_SERVICE_KEY,
    }
    peticion = urllib.request.Request(url, headers=cabeceras, method="GET")
    try:
        with urllib.request.urlopen(peticion, timeout=settings.CORE_TIMEOUT_SEG) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        if e.code in (400, 404):
            return None
        _log.warning("Error HTTP al leer de Supabase Storage (%s): %s", clave, e)
    except Exception as e:
        _log.warning("Fallo al conectar con Supabase Storage (%s): %s", clave, e)
    return None


def leer_bytes(url_o_clave: str) -> Optional[bytes]:
    """Obtiene los bytes originales de la imagen.
    1. Resuelve la clave a partir de la URL.
    2. Intenta leer del disco local (volumen montado :ro).
    3. Si no existe en disco y ALMACENAMIENTO == 'supabase', descarga desde la nube.
    """
    clave = clave_de_url(url_o_clave)
    if not clave:
        return None

    # 1. Intentar disco local primero (máxima velocidad)
    try:
        ruta = _ruta_local(clave)
        if os.path.isfile(ruta):
            with open(ruta, "rb") as f:
                return f.read()
    except (ValueError, OSError) as e:
        _log.debug("No se pudo leer localmente %s: %s", clave, e)

    # 2. Fallback a Supabase Storage
    if settings.ALMACENAMIENTO.lower() == "supabase":
        remoto = _leer_supabase(clave)
        if remoto is not None:
            return remoto

    # 3. Fallback a caché en memoria (evidencias de demostración)
    return _demo_cache.get(clave)
