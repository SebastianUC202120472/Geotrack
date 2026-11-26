import asyncio
from datetime import datetime
from typing import Dict
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.registro import obtener_logger
from app.core import almacenamiento
from app.db.database import SessionLocal
from app.db import solo_lectura_core
from app.models.cola import ColaTrabajo
from app.services import detector_evidencias, motor_auditoria

_log = obtener_logger("worker_auditoria")


def procesar_tarea_cola(db: Session, tarea: ColaTrabajo) -> bool:
    """Procesa una tarea individual de la cola de auditoría (lectura core -> storage -> motor)."""
    total_hoy = detector_evidencias.contar_analisis_hoy(db)
    if total_hoy >= settings.AUDITORIA_TOPE_DIARIO:
        tarea.estado = "OMITIDO_TOPE"
        tarea.ultimo_error = f"Tope diario alcanzado ({total_hoy}/{settings.AUDITORIA_TOPE_DIARIO})"
        tarea.actualizado_en = datetime.utcnow()
        db.commit()
        _log.info("Tarea %d omitida por tope diario (%d/%d).", tarea.id, total_hoy, settings.AUDITORIA_TOPE_DIARIO)
        return False

    tarea.estado = "PROCESANDO"
    tarea.actualizado_en = datetime.utcnow()
    db.commit()

    try:
        evidencia = solo_lectura_core.obtener_evidencia_por_id(db, tarea.evidencia_id)
        if not evidencia:
            detector_evidencias.registrar_fallo_cola(
                db, tarea.id, f"Evidencia {tarea.evidencia_id} no encontrada en el núcleo"
            )
            return False

        url_actual = evidencia.get("url_foto") or tarea.url_foto
        datos_imagen = almacenamiento.leer_bytes(url_actual)
        if datos_imagen is None:
            detector_evidencias.registrar_fallo_cola(
                db, tarea.id, f"No se pudo leer el archivo de imagen: {url_actual}"
            )
            return False

        motor_auditoria.procesar_auditoria_completa(
            db=db,
            evidencia_id=evidencia["evidencia_id"],
            pedido_id=evidencia["pedido_id"],
            url_foto=url_actual,
            datos_imagen=datos_imagen,
            fecha_entrega_declarada=evidencia.get("fecha_entrega"),
            pedido_latitud=evidencia.get("pedido_latitud"),
            pedido_longitud=evidencia.get("pedido_longitud"),
            captura_gps_app=evidencia.get("latitud_longitud_captura"),
        )

        detector_evidencias.registrar_exito_cola(db, tarea.id)
        return True

    except Exception as exc:
        _log.exception("Error inesperado procesando tarea %d (evidencia %d)", tarea.id, tarea.evidencia_id)
        db.rollback()
        detector_evidencias.registrar_fallo_cola(db, tarea.id, str(exc))
        return False


def ejecutar_ciclo_auditoria(db: Session, max_lote: int = 20) -> Dict[str, int]:
    """Ejecuta un ciclo completo: sincroniza nuevas evidencias del núcleo y procesa la cola."""
    encoladas = detector_evidencias.sincronizar_nuevas_evidencias(db, limite=max_lote)
    procesadas = 0
    fallidas = 0

    for _ in range(max_lote):
        tarea = detector_evidencias.obtener_siguiente_tarea(db)
        if not tarea:
            break
        if procesar_tarea_cola(db, tarea):
            procesadas += 1
        else:
            fallidas += 1

    return {
        "encoladas": encoladas,
        "procesadas": procesadas,
        "fallidas": fallidas,
    }


def _ejecutar_ciclo_en_sesion() -> Dict[str, int]:
    """Abre una sesión propia para el ciclo en segundo plano y la cierra al terminar."""
    db = SessionLocal()
    try:
        return ejecutar_ciclo_auditoria(db)
    finally:
        db.close()


async def bucle_worker_async(stop_event: asyncio.Event) -> None:
    """Loop periódico no bloqueante que audita evidencias en segundo plano."""
    _log.info(
        "Worker de auditoría iniciado (intervalo: %ds, tope diario: %d).",
        settings.AUDITORIA_INTERVALO_DETECCION_SEG,
        settings.AUDITORIA_TOPE_DIARIO,
    )
    while not stop_event.is_set():
        if settings.AUDITORIA_ENABLED:
            try:
                resumen = await asyncio.to_thread(_ejecutar_ciclo_en_sesion)
                if resumen["encoladas"] or resumen["procesadas"] or resumen["fallidas"]:
                    _log.info("Ciclo completado: %s", resumen)
            except Exception as exc:
                _log.exception("Fallo en ciclo periódico de auditoría: %s", exc)

        try:
            await asyncio.wait_for(stop_event.wait(), timeout=settings.AUDITORIA_INTERVALO_DETECCION_SEG)
        except asyncio.TimeoutError:
            continue

    _log.info("Worker de auditoría detenido limpiamente.")
