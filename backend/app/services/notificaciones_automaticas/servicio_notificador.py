"""Proceso principal del servicio notificador independiente.
Corre como contenedor propio sin tocar el núcleo:
1. Lee las novedades de la base de datos (cursor) y encola avisos.
2. Ejecuta el planificador (horario silencioso, resumen diario, reclamos por vencer).
3. Procesa y despacha la cola hacia los proveedores (SMTP, Telegram, WhatsApp).
"""
import time
import logging
from app.db.database import SessionLocal
from app.core.config import settings
from app.services.notificaciones_automaticas import lector, planificador, operador

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("geotrack.notificador")


def ciclo_una_vez() -> None:
    db = SessionLocal()
    try:
        # 1. Leer novedades de tablas núcleo
        nuevos = lector.ejecutar_barrido(db)
        if nuevos:
            log.info("Lector detectó %d nuevos avisos", nuevos)

        # 2. Evaluar tareas del planificador
        resumenes = planificador.ejecutar_resumen_diario(db)
        if resumenes:
            log.info("Planificador encoló %d resúmenes del día", resumenes)

        reclamos = planificador.evaluar_reclamos_por_vencer(db)
        if reclamos:
            log.info("Planificador encoló %d alertas de reclamos por vencer", reclamos)

        timeouts = planificador.evaluar_timeout_mecanicos(db)
        if timeouts:
            log.info("Planificador detectó %d mecánicos sin responder (10 min)", timeouts)

        # 3. Despachar respetando horario silencioso
        es_silencioso = planificador.en_horario_silencioso()
        resultado = operador.procesar(db, solo_urgentes=es_silencioso)
        if resultado["procesados"]:
            log.info("Despacho completado (silencioso=%s): %s", es_silencioso, resultado)

    except Exception:
        db.rollback()
        log.exception("Error en ciclo del notificador independiente")
    finally:
        db.close()


def main() -> None:
    log.info("Iniciando servicio Notificador Independiente GeoTrack...")
    intervalo = getattr(settings, "NOTIFICACIONES_INTERVALO_SEG", 30)
    while True:
        if getattr(settings, "NOTIFICACIONES_HABILITADAS", True):
            ciclo_una_vez()
        time.sleep(intervalo)


if __name__ == "__main__":
    main()
