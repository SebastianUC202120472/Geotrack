import secrets
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.chat import router as chat_router
from app.api.conversaciones import router as conversaciones_router
from app.core.config import settings
from app.core.registro import log
from app.db.database import preparar_tablas
from app.ia.proveedores import CadenaProveedores, construir_proveedores


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Arranque: tablas propias, proveedores de IA y clientes HTTP compartidos."""
    app.state.cadena = CadenaProveedores(construir_proveedores())
    app.state.http_ia = httpx.AsyncClient(timeout=settings.ASISTENTE_IA_TIMEOUT_SEG)
    app.state.http_core = httpx.AsyncClient(timeout=settings.ASISTENTE_CORE_TIMEOUT_SEG)
    if settings.ASISTENTE_ENABLED:
        try:
            preparar_tablas()
        except Exception:
            log.exception("No se pudieron preparar las tablas del asistente")
        nombres = [p.nombre for p in app.state.cadena.proveedores] or ["ninguno"]
        log.info("Asistente activo. Proveedores de IA en orden: %s", ", ".join(nombres))
    else:
        log.info("Asistente desactivado (ASISTENTE_ENABLED=false)")
    yield
    await app.state.http_ia.aclose()
    await app.state.http_core.aclose()


app = FastAPI(
    title="GeoTrack - Asistente virtual del panel",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/asistente/docs",
    openapi_url="/api/asistente/openapi.json",
    redoc_url=None,
)

if settings.cors_origins_list:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )


@app.exception_handler(Exception)
async def error_no_controlado(request: Request, exc: Exception):
    """Registra cualquier error no controlado y responde 500 con un codigo de referencia."""
    referencia = secrets.token_hex(4).upper()
    log.error("Error %s en %s %s", referencia, request.method, request.url.path, exc_info=exc)
    return JSONResponse(status_code=500, content={"detail": f"Ocurrió un error interno. Código de referencia: {referencia}"})


app.include_router(chat_router, prefix="/api/asistente", tags=["Asistente"])
app.include_router(conversaciones_router, prefix="/api/asistente/conversaciones", tags=["Historial"])


@app.get("/api/asistente/salud")
def salud():
    """Confirma que el servicio esta vivo (para Docker). Sin input."""
    return {"status": "online", "activo": settings.ASISTENTE_ENABLED}
