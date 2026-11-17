# IP del visitante y su huella anonima.
# El servicio solo se publica detras de Nginx, que escribe X-Real-IP con la IP real
# ($remote_addr) y sobrescribe lo que mande el cliente. No se usa X-Forwarded-For
# (manipulable). La IP nunca se guarda en claro: se guarda un HMAC con el secreto del modulo.
import hashlib
import hmac
import ipaddress

from fastapi import Request


def _es_ip(valor: str) -> bool:
    """Dice si un texto es una IP valida (v4 o v6). Recibe el valor."""
    try:
        ipaddress.ip_address(valor)
        return True
    except ValueError:
        return False


def ip_cliente(request: Request) -> str:
    """IP del visitante: X-Real-IP de Nginx si es valida; si no, la del par directo. Recibe la peticion."""
    real = (request.headers.get("x-real-ip") or "").strip()
    if real and len(real) <= 45 and _es_ip(real):
        return real
    return request.client.host if request.client else "desconocida"


def huella_ip(ip: str, secreto: bytes) -> str:
    """Huella irreversible de la IP (HMAC-SHA256) para contar topes sin guardar la IP. Recibe IP y secreto."""
    return hmac.new(secreto, ip.encode(), hashlib.sha256).hexdigest()
