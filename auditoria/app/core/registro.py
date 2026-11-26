import logging
import sys


def obtener_logger(nombre: str) -> logging.Logger:
    """Configura y devuelve un logger estructurado con formato estándar."""
    logger = logging.getLogger(f"auditoria.{nombre}")
    if not logger.handlers:
        manejador = logging.StreamHandler(sys.stdout)
        manejador.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(manejador)
        logger.setLevel(logging.INFO)
    return logger
