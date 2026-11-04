# Limitador en memoria (ventana deslizante) para los mensajes y audios por minuto.
# El tope diario se cuenta en la base de datos (tabla de auditoria) para que sobreviva
# a un reinicio del contenedor.
import time
from collections import OrderedDict, deque

_MAX_CLAVES = 5000


class Limitador:
    """Ventana deslizante por clave con memoria acotada. Recibe una funcion de reloj (para pruebas)."""

    def __init__(self, reloj=time.monotonic, max_claves: int = _MAX_CLAVES):
        self._reloj = reloj
        self._max_claves = max_claves
        self._eventos: OrderedDict[str, deque] = OrderedDict()

    def permitir(self, clave: str, maximo: int, ventana_seg: int) -> bool:
        """Registra un intento y dice si esta permitido. Recibe clave, maximo y ventana en segundos."""
        ahora = self._reloj()
        cola = self._eventos.pop(clave, deque())
        while cola and cola[0] <= ahora - ventana_seg:
            cola.popleft()
        permitido = len(cola) < maximo
        if permitido:
            cola.append(ahora)
        if cola:
            self._eventos[clave] = cola
            if len(self._eventos) > self._max_claves:
                self._eventos.popitem(last=False)
        return permitido


limitador = Limitador()
