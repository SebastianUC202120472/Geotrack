# Registro de eventos y errores del backend (EX-11). Escribe en consola (lo que muestra
# `docker logs`) y en un archivo rotativo, para que cada error quede con su fecha, la ruta
# que lo provoco y el detalle (traza completa).
import logging
import os
from logging.handlers import RotatingFileHandler

NOMBRE = "geotrack"
DIR_LOGS = os.getenv("LOGS_DIR", "logs")
_FORMATO = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"

_configurado = False


def configurar_registro() -> logging.Logger:
    """Configura el logger de la app una sola vez (consola + archivo rotativo). No recibe nada."""
    global _configurado
    logger = logging.getLogger(NOMBRE)
    if _configurado:
        return logger
    logger.setLevel(logging.INFO)
    formato = logging.Formatter(_FORMATO)

    consola = logging.StreamHandler()
    consola.setFormatter(formato)
    logger.addHandler(consola)

    try:
        os.makedirs(DIR_LOGS, exist_ok=True)
        archivo = RotatingFileHandler(
            os.path.join(DIR_LOGS, "geotrack.log"), maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        archivo.setFormatter(formato)
        logger.addHandler(archivo)
    except OSError as e:
        # Sin permiso de escritura (p. ej. en CI) se sigue registrando en consola.
        logger.warning("No se pudo abrir el archivo de registro: %s", e)

    logger.propagate = False
    _configurado = True
    return logger


def obtener_logger(modulo: str = "") -> logging.Logger:
    """Devuelve el logger de la app o uno hijo para un modulo. Recibe el nombre del modulo."""
    return logging.getLogger(f"{NOMBRE}.{modulo}" if modulo else NOMBRE)
