import asyncio
import os
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.db.database import engine, Base, SessionLocal
from app.models import Usuario, Pedido, Ruta, RutaDetalle
from app.services import usuario_service, parametro_service

from app.api.auth import router as auth_router
from app.api.pedidos import router as pedidos_router
from app.api.rutas import router as rutas_router
from app.api.conductor import router as conductor_router
from app.api.dashboard import router as dashboard_router
from app.api.clientes import router as clientes_router
from app.api.vehiculos import router as vehiculos_router
from app.api.correos import router as correos_router
from app.api.conductores import router as conductores_router
from app.api.reportes import router as reportes_router
from app.api.usuarios import router as usuarios_router
from app.api.parametros import router as parametros_router
from app.api.incidencias import router as incidencias_router
from app.api.recojos import router as recojos_router
from app.api.almacen import router as almacen_router
from app.api.notificaciones import router as notificaciones_router


async def tarea_limpieza_usuarios():
    """Borra cada hora usuarios @prueba.com con mas de 6 horas de antiguedad."""
    while True:
        await asyncio.sleep(3600)
        db = SessionLocal()
        try:
            hace_6_horas = datetime.utcnow() - timedelta(hours=6)
            db.query(Usuario).filter(
                Usuario.correo.like("%@prueba.com%"),
                Usuario.fecha_creacion <= hace_6_horas,
            ).delete(synchronize_session=False)
            db.commit()
            print("Limpieza de usuarios de prueba completada.")
        except Exception as e:
            db.rollback()
            print(f"Error en limpieza automática: {e}")
        finally:
            db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida: inicializa BD, admin, catalogos y tarea de limpieza al arrancar."""
    print("Esperando 5 segundos a que PostgreSQL esté 100% listo...")
    await asyncio.sleep(5)

    print("Creando tablas en la base de datos...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        usuario_service.crear_admin_inicial(db, settings.ADMIN_EMAIL, settings.ADMIN_PASSWORD)
        print(f"Admin inicial asegurado: {settings.ADMIN_EMAIL}")
        parametro_service.asegurar_motivos_iniciales(db)
        print("Catálogo de motivos de rechazo asegurado.")
        parametro_service.asegurar_combustible_inicial(db)
        print("Parámetros de combustible asegurados.")
    except Exception as e:
        print(f"No se pudo completar la inicialización: {e}")
    finally:
        db.close()

    print("Iniciando tarea de limpieza en segundo plano...")
    tarea_background = asyncio.create_task(tarea_limpieza_usuarios())

    yield

    tarea_background.cancel()


app = FastAPI(
    title="SIOL-SAVA API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS: JWT en Authorization header, sin cookies, por eso allow_credentials=False.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Compat: la app cliente puede llegar con la URL base SIN el prefijo /api. Antepone
# /api a la ruta (salvo raiz, docs y /media) para que funcione con o sin /api.
_SIN_PREFIJO = ("/", "/docs", "/redoc", "/openapi.json")


@app.middleware("http")
async def compat_prefijo_api(request: Request, call_next):
    ruta = request.scope.get("path", "")
    if not ruta.startswith("/api") and not ruta.startswith("/media") and ruta not in _SIN_PREFIJO:
        nueva = "/api" + ruta
        request.scope["path"] = nueva
        request.scope["raw_path"] = nueva.encode("utf-8")
    return await call_next(request)


os.makedirs(os.path.join("uploads", "evidencias"), exist_ok=True)
app.mount("/media", StaticFiles(directory="uploads"), name="media")

app.include_router(auth_router, prefix="/api/auth", tags=["Autenticación"])
app.include_router(clientes_router, prefix="/api/clientes", tags=["Clientes Corporativos"])
app.include_router(vehiculos_router, prefix="/api/vehiculos", tags=["Flota de Vehículos"])
app.include_router(pedidos_router, prefix="/api/pedidos", tags=["Gestión de Pedidos"])
app.include_router(rutas_router, prefix="/api/rutas", tags=["Enrutamiento y Flota"])
app.include_router(conductor_router, prefix="/api/conductor", tags=["App Móvil - Conductor"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["Dashboard y Trazabilidad"])
app.include_router(correos_router, prefix="/api/correos", tags=["Bandeja de Correos"])
app.include_router(conductores_router, prefix="/api/conductores", tags=["Conductores"])
app.include_router(reportes_router, prefix="/api/reportes", tags=["Reportes"])
app.include_router(usuarios_router, prefix="/api/usuarios", tags=["Usuarios del Panel"])
app.include_router(parametros_router, prefix="/api/parametros", tags=["Parámetros"])
app.include_router(incidencias_router, prefix="/api/incidencias", tags=["Incidencias"])
app.include_router(recojos_router, prefix="/api/recojos", tags=["Recojos Inbound"])
app.include_router(almacen_router, prefix="/api/almacen", tags=["Almacén (Ingreso)"])
app.include_router(notificaciones_router, prefix="/api/notificaciones", tags=["Notificaciones"])


@app.get("/")
def health_check():
    """Confirma que el backend esta vivo."""
    return {"status": "online", "message": "Backend SIOL-SAVA operativo"}
