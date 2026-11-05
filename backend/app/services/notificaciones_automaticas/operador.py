"""Operador de todo: crea los avisos en BD en el momento justo y los procesa despues."""
import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories import notificacion_envio_repository
from app.services.notificaciones_automaticas.constructor import construir_mensaje
from app.services.notificaciones_automaticas import proveedores

# Hijo del logger "geotrack": hereda su consola y su archivo rotativo.
log = logging.getLogger("geotrack.notificaciones")


def registrar(db: Session, evento: str, contexto: dict) -> int:
    """Crea en BD los mensajes de un evento; devuelve cuantos inserto. No duplica.
    Best-effort: nunca lanza. Si algo falla deshace solo los avisos (el evento del negocio
    ya fue confirmado por el servicio que llama) y deja el error en el registro."""
    if not settings.NOTIFICACIONES_HABILITADAS:
        return 0
    try:
        creados = 0
        for mensaje in construir_mensaje(evento, contexto, db):
            if notificacion_envio_repository.crear_si_no_existe(db, mensaje):
                creados += 1
        db.commit()
        return creados
    except Exception:
        db.rollback()
        log.exception("No se pudo registrar el aviso %s", evento)
        return 0


def procesar(db: Session, solo_urgentes: bool = False) -> dict:
    """Reclama pendientes, los entrega por su proveedor y actualiza el resultado.
    Si solo_urgentes es True, omite los avisos normales hasta la mañana."""
    pendientes = notificacion_envio_repository.listar_pendientes(db, solo_urgentes=solo_urgentes)
    enviados = 0
    fallidos = 0
    reprogramados = 0
    for fila in pendientes:
        try:
            proveedores.enviar(fila)
            notificacion_envio_repository.marcar_enviado(db, fila)
            enviados += 1
        except Exception as exc:
            reintentable = proveedores.es_error_transitorio(exc)
            notificacion_envio_repository.marcar_fallido(db, fila, str(exc), reintentable)
            if not reintentable or (fila.intentos or 0) >= notificacion_envio_repository.MAX_INTENTOS:
                fallidos += 1
            else:
                reprogramados += 1
            log.warning("Aviso %s (%s) no entregado, intento %s: %s",
                        fila.id, fila.evento, fila.intentos, exc)
        # Se confirma fila por fila: si el proceso cae a mitad del lote, lo ya enviado
        # queda marcado y no se reenvia al vencer la concesion.
        db.commit()
    return {
        "procesados": len(pendientes),
        "enviados": enviados,
        "reprogramados": reprogramados,
        "fallidos": fallidos,
    }
