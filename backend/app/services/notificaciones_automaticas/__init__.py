"""Centro de notificaciones automaticas: el lector crea los avisos en BD y el notificador los envia."""
from app.services.notificaciones_automaticas.operador import log, procesar, registrar

__all__ = ["registrar", "procesar", "log"]
