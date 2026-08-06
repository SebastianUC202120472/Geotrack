# Limitador de peticiones en memoria (ventana deslizante simple) para endpoints
# publicos. Single-instance (el contenedor no usa Redis). La clase es testeable
# inyectando un reloj; el modulo expone una dependencia FastAPI lista para usar.
import ipaddress
import time
from collections import deque, OrderedDict

from fastapi import Request, HTTPException

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


def _es_ip(valor: str) -> bool:
    """Dice si un string es una IP valida (v4 o v6). Recibe el valor."""
    try:
        ipaddress.ip_address(valor)
        return True
    except ValueError:
        return False


def _ip_cliente(request: Request) -> str:
    """Obtiene la IP del cliente para la clave del limitador. Recibe la request.
    Detras de Nginx toda peticion llega de la IP del contenedor, asi que se usa el
    X-Real-IP que Nginx pone ($remote_addr, valor unico que Nginx sobrescribe), NO la
    lista X-Forwarded-For (manipulable por el cliente). Solo se acepta si es una IP
    valida; si no, se cae a la IP del peer directo."""
    real = (request.headers.get("x-real-ip") or "").strip()
    if real and len(real) <= 45 and _es_ip(real):
        return real
    return request.client.host if request.client else "?"


def limite_publico(maximo: int = 30, ventana_seg: int = 60):
    """Devuelve una dependencia FastAPI que limita por IP+ruta. Recibe maximo y ventana."""

    def _dep(request: Request):
        clave = f"{_ip_cliente(request)}:{request.scope.get('path', '')}"
        if not _singleton.permitir(clave, maximo, ventana_seg):
            raise HTTPException(status_code=429, detail="Demasiadas solicitudes. Intente en un momento.")

    return _dep
