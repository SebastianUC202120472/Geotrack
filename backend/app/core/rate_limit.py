# Limitador de peticiones en memoria (ventana deslizante simple) para endpoints
# publicos. Single-instance (el contenedor no usa Redis). La clase es testeable
# inyectando un reloj; el modulo expone una dependencia FastAPI lista para usar.
import ipaddress
import logging
import time
from collections import deque, OrderedDict
from functools import lru_cache

from fastapi import Request, HTTPException

from app.core.config import settings

log = logging.getLogger(__name__)

# Tope duro de claves distintas que se guardan a la vez. Acota la memoria ante
# muchas IPs (o entradas basura): al superarlo se desaloja la clave mas antigua
# (LRU). Ademas las colas vacias se descartan tras purgarlas.
_MAX_CLAVES = 10000


class _Limitador:
    """Ventana deslizante por clave, con memoria acotada (LRU). Recibe una funcion de reloj (para tests)."""

    def __init__(self, reloj=time.time, max_claves: int = _MAX_CLAVES):
        self._reloj = reloj
        self._max_claves = max_claves
        self._eventos = OrderedDict()  # clave -> deque de timestamps (orden de uso)

    def permitir(self, clave: str, maximo: int, ventana_seg: int) -> bool:
        """Registra un intento y dice si esta permitido. Recibe clave, maximo y ventana en seg."""
        ahora = self._reloj()
        limite = ahora - ventana_seg
        cola = self._eventos.get(clave)
        if cola is None:
            cola = deque()
        else:
            self._eventos.move_to_end(clave)  # marca como usada recientemente (LRU)
        while cola and cola[0] < limite:
            cola.popleft()
        permitido = len(cola) < maximo
        if permitido:
            cola.append(ahora)
        if cola:
            self._eventos[clave] = cola
            self._eventos.move_to_end(clave)
            # Desaloja la clave menos usada si se supero el tope.
            if len(self._eventos) > self._max_claves:
                self._eventos.popitem(last=False)
        else:
            # Cola vacia (ventana expirada): no conservar la clave.
            self._eventos.pop(clave, None)
        return permitido


_singleton = _Limitador()


def limitar(clave: str, maximo: int, ventana_seg: int) -> bool:
    """Atajo sobre el limitador global. Recibe clave, maximo y ventana."""
    return _singleton.permitir(clave, maximo, ventana_seg)


def _ip(valor: str):
    """Convierte un texto en IP (v4 o v6; una IPv4 escrita como IPv6 se normaliza a v4), o None si no
    es una IP valida. Recibe el valor."""
    try:
        ip = ipaddress.ip_address((valor or "").strip())
    except ValueError:
        return None
    return getattr(ip, "ipv4_mapped", None) or ip


def _es_ip(valor: str) -> bool:
    """Dice si un string es una IP valida (v4 o v6). Recibe el valor."""
    return _ip(valor) is not None


@lru_cache(maxsize=8)
def _redes_de_confianza(texto: str) -> tuple:
    """Redes de PROXIES_DE_CONFIANZA ya interpretadas; una entrada invalida se ignora y se avisa en el
    log. Recibe el texto de la variable."""
    redes = []
    for parte in (texto or "").split(","):
        parte = parte.strip()
        if not parte:
            continue
        try:
            redes.append(ipaddress.ip_network(parte, strict=False))
        except ValueError:
            log.warning("PROXIES_DE_CONFIANZA: se ignora la entrada invalida %r", parte)
    return tuple(redes)


def _de_confianza(ip) -> bool:
    """Dice si la IP del peer directo es de un proxy de confianza. Recibe la IP (o None)."""
    if ip is None:
        return False
    return any(ip.version == red.version and ip in red for red in _redes_de_confianza(settings.PROXIES_DE_CONFIANZA))


def _ip_cliente(request: Request) -> str:
    """Obtiene la IP del cliente para la clave del limitador. Recibe la request.
    Detras de Nginx toda peticion llega de la IP del contenedor, asi que se usa el
    X-Real-IP que Nginx pone ($remote_addr, valor unico que Nginx sobrescribe), NO la
    lista X-Forwarded-For (manipulable por el cliente). La cabecera solo se acepta si la
    peticion viene de una red de PROXIES_DE_CONFIANZA (Nginx o un servicio interno) y trae
    una IP valida; en cualquier otro caso cuenta la IP del peer directo, para que quien
    llegue al backend sin pasar por Nginx no pueda inventarse una IP en cada peticion."""
    peer = request.client.host if request.client else ""
    if _de_confianza(_ip(peer)):
        real = (request.headers.get("x-real-ip") or "").strip()
        if real and len(real) <= 45 and _es_ip(real):
            return real
    return peer or "?"


def limite_publico(maximo: int = 30, ventana_seg: int = 60):
    """Devuelve una dependencia FastAPI que limita por IP+ruta. Recibe maximo y ventana."""

    def _dep(request: Request):
        clave = f"{_ip_cliente(request)}:{request.scope.get('path', '')}"
        if not _singleton.permitir(clave, maximo, ventana_seg):
            raise HTTPException(status_code=429, detail="Demasiadas solicitudes. Intente en un momento.")

    return _dep
