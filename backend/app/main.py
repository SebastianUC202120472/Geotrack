# app/main.py
# - Crea la app FastAPI y configura CORS (permite que la Web y la App Móvil llamen a la API desde otro origen).
import asyncio
import os
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.db.database import engine, Base, SessionLocal
# Importar los modelos registra sus tablas en Base.metadata (necesario para create_all).
from app.models import Usuario, Pedido, Ruta, RutaDetalle
from app.services import usuario_service

# Routers (cada uno agrupa los endpoints de un módulo).
from app.api.auth import router as auth_router
from app.api.pedidos import router as pedidos_router
from app.api.rutas import router as rutas_router
from app.api.conductor import router as conductor_router
from app.api.dashboard import router as dashboard_router  # Fase 4: trazabilidad
from app.api.clientes import router as clientes_router    # Fase 4: clientes corporativos
from app.api.vehiculos import router as vehiculos_router  # Fase 4: flota de vehículos
from app.api.correos import router as correos_router      # Bandeja de solicitudes de recojo
from app.api.conductores import router as conductores_router  # Gestión de conductores


async def tarea_limpieza_usuarios():
    """
    Tarea en segundo plano: cada hora borra los usuarios de prueba
    (@prueba.com) con más de 6 horas de antigüedad. Mantiene limpia la BD del MVP.
    """
    while True:
        await asyncio.sleep(3600)  # espera 1 hora
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
    """
    Ciclo de vida de la app. El código antes de 'yield' corre al ARRANCAR;
    el de después corre al APAGAR.
    """
    # Docker puede levantar la app antes de que PostgreSQL esté listo:
    # esperamos unos segundos para evitar el error de conexión inicial.
    print("Esperando 5 segundos a que PostgreSQL esté 100% listo...")
    await asyncio.sleep(5)

    # Crea las tablas que aún no existan (no modifica las ya creadas).
    print("Creando tablas en la base de datos...")
    Base.metadata.create_all(bind=engine)

    # Crea el admin inicial si no existe (para poder entrar, ya que el registro
    # está restringido a admins). Sus credenciales vienen de variables de entorno.
    db = SessionLocal()
    try:
        usuario_service.crear_admin_inicial(db, settings.ADMIN_EMAIL, settings.ADMIN_PASSWORD)
        print(f"Admin inicial asegurado: {settings.ADMIN_EMAIL}")
    except Exception as e:
        print(f"No se pudo crear el admin inicial: {e}")
    finally:
        db.close()

    # Arranca la limpieza periódica en segundo plano.
    print("Iniciando tarea de limpieza en segundo plano...")
    tarea_background = asyncio.create_task(tarea_limpieza_usuarios())

    yield  # <-- aquí la app queda atendiendo peticiones

    # Al apagar, cancelamos la tarea de fondo.
    tarea_background.cancel()


# --- Creación de la app ---
app = FastAPI(
    title="SIOL-SAVA API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS: permite que el frontend (otro origen) consuma la API.
# Los orígenes vienen de la config (CORS_ORIGINS). allow_credentials=False porque
# usamos JWT en el header Authorization (no cookies): así '*' sigue siendo válido
# y NO complica al frontend, evitando el combo inseguro '*' + credentials=True.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir las evidencias POD (CUS-29) como archivos estáticos en /media.
os.makedirs(os.path.join("uploads", "evidencias"), exist_ok=True)
app.mount("/media", StaticFiles(directory="uploads"), name="media")

# Registro de routers. Cada 'prefix' es la base de las URLs de ese módulo.
app.include_router(auth_router, prefix="/api/auth", tags=["Autenticación"])
app.include_router(clientes_router, prefix="/api/clientes", tags=["Clientes Corporativos"])
app.include_router(vehiculos_router, prefix="/api/vehiculos", tags=["Flota de Vehículos"])
app.include_router(pedidos_router, prefix="/api/pedidos", tags=["Gestión de Pedidos"])
app.include_router(rutas_router, prefix="/api/rutas", tags=["Enrutamiento y Flota"])
app.include_router(conductor_router, prefix="/api/conductor", tags=["App Móvil - Conductor"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["Dashboard y Trazabilidad"])
app.include_router(correos_router, prefix="/api/correos", tags=["Bandeja de Correos"])
app.include_router(conductores_router, prefix="/api/conductores", tags=["Conductores"])


@app.get("/")
def health_check():
    """Endpoint de salud: confirma rápidamente que el backend está vivo."""
    return {"status": "online", "message": "Backend SIOL-SAVA operativo"}
