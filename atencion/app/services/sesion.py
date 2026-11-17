# Estado en memoria de cada conversacion: lo que NO debe ir a la base ni al modelo.
#   - tokens de portal de los pedidos que el visitante verifico (15 min, los emite el nucleo),
#   - seudonimos (valor real de [CORREO_1], [TEL_1]),
#   - propuestas pendientes con sus datos reales (hasta que el visitante confirme o cancele),
#   - contadores anti-abuso (verificaciones, acciones, audios) y fallos seguidos sin resolver.
# Vive en el proceso: con un solo worker (como el resto del sistema) es suficiente. Si el
# contenedor se reinicia, el visitante vuelve a verificar y las propuestas pendientes vencen.
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field

from app.services.privacidad import Seudonimos

_MAX_CONVERSACIONES = 5000
_VIDA_SEG = 3 * 3600
# El token de portal dura 15 min en el nucleo; aqui se olvida un poco antes para no usarlo vencido.
_VIDA_TOKEN_PORTAL_SEG = 14 * 60


@dataclass
class Propuesta:
    """Accion que el visitante tiene que confirmar con un clic (reprogramar o registrar contacto)."""
    id: str
    tipo: str
    datos: dict
    vence: float


@dataclass
class EstadoConversacion:
    """Lo que el servidor recuerda de una conversacion mientras esta viva."""
    seudonimos: Seudonimos = field(default_factory=Seudonimos)
    pedidos: dict[str, tuple[str, float]] = field(default_factory=dict)   # codigo -> (token, vence)
    propuestas: dict[str, Propuesta] = field(default_factory=dict)
    verificaciones: int = 0
    acciones: int = 0
    audios: int = 0
    fallos_seguidos: int = 0
    usado: float = field(default_factory=time.monotonic)

    def guardar_token(self, codigo: str, token: str, reloj=time.monotonic) -> None:
        """Recuerda el token de portal de un pedido verificado. Recibe codigo y token."""
        self.pedidos[codigo] = (token, reloj() + _VIDA_TOKEN_PORTAL_SEG)

    def token(self, codigo: str, reloj=time.monotonic) -> str | None:
        """Token vigente de un pedido verificado, o None. Recibe el codigo."""
        guardado = self.pedidos.get(codigo)
        if not guardado or guardado[1] <= reloj():
            self.pedidos.pop(codigo, None)
            return None
        return guardado[0]

    def olvidar_token(self, codigo: str) -> None:
        """Olvida el token de un pedido (vencio en el nucleo). Recibe el codigo."""
        self.pedidos.pop(codigo, None)

    def propuesta(self, ident: str, reloj=time.monotonic) -> Propuesta | None:
        """Propuesta pendiente y vigente, o None. Recibe su id."""
        p = self.propuestas.get(ident)
        if p and p.vence <= reloj():
            self.propuestas.pop(ident, None)
            return None
        return p


class Sesiones:
    """Estados por conversacion con memoria acotada (LRU) y vida maxima."""

    def __init__(self, reloj=time.monotonic):
        """Empieza vacio. Recibe un reloj (pruebas)."""
        self._reloj = reloj
        self._estados: OrderedDict[str, EstadoConversacion] = OrderedDict()
        self._candado = threading.Lock()

    def de(self, conversacion_id: str) -> EstadoConversacion:
        """Estado de una conversacion (lo crea si no existe). Recibe el id."""
        ahora = self._reloj()
        with self._candado:
            estado = self._estados.pop(conversacion_id, None)
            if estado is None or ahora - estado.usado > _VIDA_SEG:
                estado = EstadoConversacion()
            estado.usado = ahora
            self._estados[conversacion_id] = estado
            while len(self._estados) > _MAX_CONVERSACIONES:
                self._estados.popitem(last=False)
            return estado

    def limpiar(self) -> None:
        """Olvida todo (pruebas). Sin input."""
        with self._candado:
            self._estados.clear()


sesiones = Sesiones()
