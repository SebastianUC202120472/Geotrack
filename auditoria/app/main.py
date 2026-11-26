import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.registro import obtener_logger
from app.db.database import preparar_tablas
from app.services.worker_auditoria import bucle_worker_async
from app.api.router import router as auditoria_router

_log = obtener_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicialización del servicio de auditoría, su esquema propio y worker periódico."""
    _log.info("Iniciando servicio de Auditoría de Evidencias...")
    stop_event = asyncio.Event()
    worker_task = None

    try:
        preparar_tablas()
    except Exception as e:
        _log.exception("Error al preparar tablas de auditoría: %s", e)

    if settings.AUDITORIA_ENABLED and settings.AUDITORIA_WORKER_ENABLED:
        worker_task = asyncio.create_task(bucle_worker_async(stop_event))

    try:
        yield
    finally:
        stop_event.set()
        if worker_task is not None:
            try:
                await asyncio.wait_for(worker_task, timeout=5.0)
            except asyncio.TimeoutError:
                worker_task.cancel()
        _log.info("Cerrando servicio de Auditoría de Evidencias.")


app = FastAPI(
    title="GeoTrack - Auditoría Inteligente de Evidencias con IA",
    description="Microservicio autónomo de control de calidad, detección de fraude y auditoría fotográfica.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.AUDITORIA_ENABLED else None,
)

# CORS restringido explícitamente por variable de entorno (en Docker todo entra por mismo origen vía Nginx)
_origenes = [o.strip() for o in settings.AUDITORIA_CORS_ORIGINS.split(",") if o.strip()]
if _origenes:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_origenes,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/salud")
def healthcheck():
    """Estado de salud del microservicio."""
    return {
        "estado": "operativo" if settings.AUDITORIA_ENABLED else "desactivado",
        "servicio": "auditoria-evidencias",
        "esquema_bd": settings.AUDITORIA_DB_SCHEMA,
    }


app.include_router(auditoria_router)
