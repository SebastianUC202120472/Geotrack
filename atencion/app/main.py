import asyncio
import secrets
from contextlib import asynccontextmanager, suppress

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.admin import router as admin_router
from app.api.chat import router as chat_router
from app.api.gestion import router as gestion_router
from app.api.deps import CABECERA_CONVERSACION
from app.conocimiento import servicio as servicio_conocimiento
from app.core.config import settings
from app.core.registro import log
from app.db.database import SessionLocal
from app.ia.fabrica import config_ia, crear_cadena
from app.ia.proveedores import timeout_http
from app.repositories import conversacion_repository


def preparar_conocimiento() -> None:
    """Prepara la base de conocimiento y deja constancia en el log. Sin input."""
    cargados, activos = servicio_conocimiento.preparar_conocimiento()
    if cargados:
        log.info("Base de conocimiento inicial cargada: %s artículos", cargados)
    log.info("Índice de la base de conocimiento: %s artículos activos", activos)


def purgar_conversaciones() -> int:
    """Borra las conversaciones mas antiguas que la retencion configurada (Ley 29733). Sin input."""
    db = SessionLocal()
    try:
        return conversacion_repository.purgar_antiguas(db, settings.ATENCION_RETENCION_DIAS)
    finally:
        db.close()


async def _tarea_purga() -> None:
    """Cada cierto tiempo borra las conversaciones vencidas, sin detener el servicio si falla. Sin input."""
    while True:
        try:
            borradas = await asyncio.to_thread(purgar_conversaciones)
            if borradas:
                log.info("Retención: %s conversaciones antiguas borradas", borradas)
        except Exception:
            log.exception("No se pudieron borrar las conversaciones antiguas")
        await asyncio.sleep(settings.ATENCION_PURGA_CADA_MIN * 60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Arranque: tablas propias, base de conocimiento, proveedores de IA, cliente HTTP y purga."""
    app.state.cadena = crear_cadena()
    app.state.http_ia = httpx.AsyncClient(timeout=timeout_http(config_ia()))
    app.state.http_core = httpx.AsyncClient(timeout=settings.ATENCION_CORE_TIMEOUT_SEG)
    purga = None
    if settings.ATENCION_ENABLED:
        try:
            await asyncio.to_thread(preparar_conocimiento)
        except Exception:
            log.exception("No se pudo preparar la base de conocimiento del asistente de atención")
        purga = asyncio.create_task(_tarea_purga())
        nombres = [p.nombre for p in app.state.cadena.proveedores] or ["ninguno (solo base de conocimiento)"]
        log.info("Asistente de atención activo. Proveedores de IA en orden: %s", ", ".join(nombres))
    else:
        log.info("Asistente de atención desactivado (ATENCION_ENABLED=false)")
    yield
    if purga:
        purga.cancel()
        with suppress(asyncio.CancelledError):
            await purga
    await app.state.http_ia.aclose()
    await app.state.http_core.aclose()


app = FastAPI(
    title="SAVA - Asistente virtual de atención al cliente",
    version="0.1.0",
    lifespan=lifespan,
    # Servicio publico: la documentacion interactiva no se publica.
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

if settings.cors_origins_list:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT"],
        allow_headers=["Content-Type", "Authorization", CABECERA_CONVERSACION],
    )


@app.middleware("http")
async def cabeceras_seguridad(request: Request, call_next):
    """Agrega cabeceras de seguridad a todas las respuestas. Recibe la peticion."""
    respuesta = await call_next(request)
    respuesta.headers.setdefault("X-Content-Type-Options", "nosniff")
    respuesta.headers.setdefault("Cache-Control", "no-store")
    respuesta.headers.setdefault("Referrer-Policy", "no-referrer")
    return respuesta


@app.exception_handler(Exception)
async def error_no_controlado(request: Request, exc: Exception):
    """Registra cualquier error no controlado y responde 500 con un codigo de referencia."""
    referencia = secrets.token_hex(4).upper()
    log.error("Error %s en %s %s", referencia, request.method, request.url.path, exc_info=exc)
    return JSONResponse(status_code=500, content={"detail": f"Ocurrió un error interno. Código de referencia: {referencia}"})


app.include_router(chat_router, prefix="/api/atencion", tags=["Atención al cliente"])
app.include_router(gestion_router, prefix="/api/atencion", tags=["Portal, acciones y voz"])
app.include_router(admin_router, prefix="/api/atencion/admin", tags=["Administración (panel)"])


@app.get("/api/atencion/salud")
def salud():
    """Confirma que el servicio esta vivo (para Docker). Sin input."""
    return {"status": "online", "activo": settings.ATENCION_ENABLED}
