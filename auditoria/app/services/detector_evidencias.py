from datetime import datetime, date, timedelta
from typing import List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.registro import obtener_logger
from app.models.analisis import EvidenciaAnalisis
from app.models.cola import ColaTrabajo
from app.db import solo_lectura_core

_log = obtener_logger("detector_evidencias")


def contar_analisis_hoy(db: Session) -> int:
    """Devuelve la cantidad de evidencias analizadas el día de hoy."""
    hoy = date.today()
    return db.query(func.count(EvidenciaAnalisis.id)).filter(
        func.date(EvidenciaAnalisis.creado_en) == hoy
    ).scalar() or 0


def sincronizar_nuevas_evidencias(db: Session, limite: int = 50) -> int:
    """Detecta evidencias en el núcleo que aún no han sido analizadas (o cuya foto fue actualizada)
    y las encola en cola_trabajo.
    """
    total_hoy = contar_analisis_hoy(db)
    if total_hoy >= settings.AUDITORIA_TOPE_DIARIO:
        _log.info(
            "Tope diario alcanzado (%d/%d). Se omite sincronización de nuevas evidencias por hoy.",
            total_hoy,
            settings.AUDITORIA_TOPE_DIARIO,
        )
        return 0

    candidatas = solo_lectura_core.obtener_evidencias_recientes(db, limite=limite)
    encoladas = 0

    for ev in candidatas:
        ev_id = ev["evidencia_id"]
        url_foto = ev["url_foto"]
        pedido_id = ev["pedido_id"]

        # Verificar si ya fue analizada con esta misma URL
        ya_analizada = db.query(EvidenciaAnalisis.id).filter(
            EvidenciaAnalisis.evidencia_id == ev_id,
            EvidenciaAnalisis.url_foto == url_foto,
        ).first()

        if ya_analizada:
            continue

        # Verificar si ya está en cola pendiente
        item_cola = db.query(ColaTrabajo).filter(ColaTrabajo.evidencia_id == ev_id).first()

        if not item_cola:
            item_cola = ColaTrabajo(
                evidencia_id=ev_id,
                pedido_id=pedido_id,
                url_foto=url_foto,
                estado="PENDIENTE",
            )
            db.add(item_cola)
            encoladas += 1
        elif item_cola.url_foto != url_foto:
            # Si la foto cambió en el núcleo, resetear estado en cola para reanalizar
            item_cola.url_foto = url_foto
            item_cola.estado = "PENDIENTE"
            item_cola.intentos = 0
            item_cola.ultimo_error = None
            item_cola.programado_para = datetime.utcnow()
            encoladas += 1

    if encoladas > 0:
        db.commit()
        _log.info("Se encolaron %d nuevas evidencias para auditoría.", encoladas)

    return encoladas


def obtener_siguiente_tarea(db: Session) -> Optional[ColaTrabajo]:
    """Obtiene la siguiente evidencia lista para ser procesada."""
    ahora = datetime.utcnow()
    return db.query(ColaTrabajo).filter(
        ColaTrabajo.estado == "PENDIENTE",
        ColaTrabajo.programado_para <= ahora,
    ).order_by(ColaTrabajo.id.asc()).first()


def registrar_exito_cola(db: Session, cola_id: int):
    """Marca la tarea de la cola como completada."""
    tarea = db.query(ColaTrabajo).filter(ColaTrabajo.id == cola_id).first()
    if tarea:
        tarea.estado = "COMPLETADO"
        tarea.actualizado_en = datetime.utcnow()
        db.commit()


def registrar_fallo_cola(db: Session, cola_id: int, error_mensaje: str):
    """Registra fallo en la tarea con reintento exponencial."""
    tarea = db.query(ColaTrabajo).filter(ColaTrabajo.id == cola_id).first()
    if not tarea:
        return

    tarea.intentos += 1
    tarea.ultimo_error = error_mensaje
    tarea.actualizado_en = datetime.utcnow()

    if tarea.intentos >= settings.AUDITORIA_MAX_REINTENTOS:
        tarea.estado = "FALLIDO"
        _log.warning("Tarea %d (evidencia %d) marcada como FALLIDA tras %d intentos.", tarea.id, tarea.evidencia_id, tarea.intentos)
    else:
        # Backoff exponencial: 1m, 2m, 4m...
        segundos_espera = min(3600, 60 * (2 ** (tarea.intentos - 1)))
        tarea.programado_para = datetime.utcnow() + timedelta(seconds=segundos_espera)
        tarea.estado = "PENDIENTE"
        _log.info("Tarea %d reintentará en %d segundos.", tarea.id, segundos_espera)

    db.commit()
