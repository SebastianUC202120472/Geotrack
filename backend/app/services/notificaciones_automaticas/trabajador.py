"""Trabajador en segundo plano: busca y procesa los avisos pendientes cada cierto tiempo."""
import asyncio
import logging

from app.db.database import SessionLocal
from app.services.notificaciones_automaticas import operador

log = logging.getLogger("geotrack.notificaciones")


def _procesar_una_vez() -> None:
    """Abre su propia sesion y procesa la cola. Es sincrono: corre en un hilo aparte."""
    db = SessionLocal()
    try:
        resultado = operador.procesar(db)
        if resultado["procesados"]:
            log.info("Avisos procesados: %s", resultado)
    except Exception:
        db.rollback()
        log.exception("Fallo el ciclo del trabajador de notificaciones")
    finally:
        db.close()


async def ejecutar(intervalo_seg: int, habilitado: bool) -> None:
    """Bucle que cada intervalo procesa la cola de avisos.
    Las consultas y los envios (SMTP/Telegram) son bloqueantes, por eso se delegan a un hilo:
    asi no se congela el bucle de eventos de la API ni de Socket.IO mientras se envia."""
    while True:
        if habilitado:
            await asyncio.to_thread(_procesar_una_vez)
        await asyncio.sleep(intervalo_seg)
