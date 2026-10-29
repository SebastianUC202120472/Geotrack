# Enlaces firmados con vencimiento para las fotos (EX-03). /media ya no es publico: cada URL
# "/media/..." que sale en una respuesta JSON de la API se firma con HMAC y vence en unas horas.
# El vencimiento se redondea a bloques de una hora para que la misma foto conserve la misma URL
# entre refrescos (el panel y la app consultan cada pocos segundos y aprovechan la cache).
import base64
import hashlib
import hmac
import json
import time

from app.core.config import settings

PREFIJO = "/media/"
BLOQUE_SEG = 3600
VIGENCIA_BLOQUES = 3  # entre 2 y 3 horas de validez


def _firma(ruta: str, exp: int) -> str:
    """Firma HMAC-SHA256 de la ruta y el vencimiento. Recibe la ruta (sin parametros) y exp."""
    mac = hmac.new(settings.SECRET_KEY.encode(), f"{ruta}|{exp}".encode(), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(mac[:18]).decode().rstrip("=")


def firmar(url: str, ahora: float | None = None) -> str:
    """Agrega exp y firma a una URL "/media/...". Las demas cadenas no cambian. Recibe la URL."""
    if not isinstance(url, str) or not url.startswith(PREFIJO) or "firma=" in url:
        return url
    ruta, _, query = url.partition("?")
    exp = (int(ahora if ahora is not None else time.time()) // BLOQUE_SEG + VIGENCIA_BLOQUES) * BLOQUE_SEG
    extra = f"exp={exp}&firma={_firma(ruta, exp)}"
    return f"{ruta}?{query}&{extra}" if query else f"{ruta}?{extra}"


def verificar(ruta: str, exp: int, firma: str, ahora: float | None = None) -> bool:
    """True si la firma corresponde a la ruta y aun no vence. Recibe la ruta, exp y la firma."""
    if not firma or exp < int(ahora if ahora is not None else time.time()):
        return False
    return hmac.compare_digest(_firma(ruta, exp), firma)


def firmar_en(datos):
    """Recorre un JSON ya decodificado y firma toda cadena "/media/...". Recibe dict, lista o valor."""
    if isinstance(datos, dict):
        return {k: firmar_en(v) for k, v in datos.items()}
    if isinstance(datos, list):
        return [firmar_en(v) for v in datos]
    if isinstance(datos, str):
        return firmar(datos)
    return datos


def firmar_cuerpo(cuerpo: bytes) -> bytes | None:
    """Firma las URLs de un cuerpo JSON. Devuelve el cuerpo nuevo o None si no hay nada que firmar."""
    if b'"/media/' not in cuerpo:
        return None
    try:
        datos = json.loads(cuerpo)
    except ValueError:
        return None
    return json.dumps(firmar_en(datos), ensure_ascii=False, separators=(",", ":")).encode()
