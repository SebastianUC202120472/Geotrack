# Limitador de peticiones en memoria (ventana deslizante simple) para endpoints
# publicos. Single-instance (el contenedor no usa Redis). La clase es testeable
# inyectando un reloj; el modulo expone una dependencia FastAPI lista para usar.
import time
from collections import defaultdict, deque

from fastapi import Request, HTTPException


class _Limitador:
    """Ventana deslizante por clave. Recibe una funcion de reloj (para tests)."""

    def __init__(self, reloj=time.time):
        self._reloj = reloj
        self._eventos = defaultdict(deque)

    def permitir(self, clave: str, maximo: int, ventana_seg: int) -> bool:
        """Registra un intento y dice si esta permitido. Recibe clave, maximo y ventana en seg."""
        ahora = self._reloj()
        cola = self._eventos[clave]
        limite = ahora - ventana_seg
        while cola and cola[0] < limite:
            cola.popleft()
        if len(cola) >= maximo:
            return False
        cola.append(ahora)
        return True


_singleton = _Limitador()


def limitar(clave: str, maximo: int, ventana_seg: int) -> bool:
    """Atajo sobre el limitador global. Recibe clave, maximo y ventana."""
    return _singleton.permitir(clave, maximo, ventana_seg)


def limite_publico(maximo: int = 30, ventana_seg: int = 60):
    """Devuelve una dependencia FastAPI que limita por IP+ruta. Recibe maximo y ventana."""

    def _dep(request: Request):
        ip = request.client.host if request.client else "?"
        clave = f"{ip}:{request.scope.get('path', '')}"
        if not _singleton.permitir(clave, maximo, ventana_seg):
            raise HTTPException(status_code=429, detail="Demasiadas solicitudes. Intente en un momento.")

    return _dep
