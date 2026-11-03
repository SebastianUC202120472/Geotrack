"""Centro de notificaciones automaticas: crea avisos en BD y un trabajador los envia."""
from app.services.notificaciones_automaticas.operador import log, procesar, registrar

__all__ = ["registrar", "procesar", "log"]
