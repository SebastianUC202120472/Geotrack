import logging
import sys


def configurar_registro() -> logging.Logger:
    """Configura el registro del servicio en la salida estandar. Sin input."""
    log = logging.getLogger("asistente")
    if not log.handlers:
        manejador = logging.StreamHandler(sys.stdout)
        manejador.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
        log.addHandler(manejador)
        log.setLevel(logging.INFO)
    return log


log = configurar_registro()
