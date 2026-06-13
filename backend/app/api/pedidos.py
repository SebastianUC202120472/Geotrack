# app/api/pedidos.py
# ============================================================================
# CAPA: API / ROUTER (puerta de entrada HTTP) — Clean Architecture
# ----------------------------------------------------------------------------
# ¿QUÉ HACE?  Expone las URLs del módulo Inbound (gestión de pedidos del admin):
#               POST /api/pedidos/upload        -> cargar Excel (CUS-13)
#               POST /api/pedidos/geocodificar  -> calcular coordenadas (CUS-15)
#               GET  /api/pedidos/              -> listar pedidos
#               GET  /api/pedidos/zonas         -> agrupar por distrito (CUS-16)
# ¿CÓMO?      Endpoints delgados: validan permisos y delegan al SERVICIO.
# SEGURIDAD:  TODOS exigen rol 'admin' (Depends(get_current_admin)).
# ¿CON QUÉ SE CONECTA?
#   - services/pedido_service.py -> la lógica real.
#   - schemas/pedido.py          -> moldes de respuesta (response_model).
#   - api/deps.py                -> control de acceso por rol.
#   - Lo registra: main.py con el prefijo /api/pedidos.
# ============================================================================
from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_current_admin
from app.models.usuario import Usuario
from app.services import pedido_service
from app.schemas.pedido import (
    PedidoResponse,
    CargaPedidosResponse,
    GeocodificacionResponse,
    ZonasResponse,
)
from typing import List

router = APIRouter()


@router.post("/upload", response_model=CargaPedidosResponse)
async def upload_pedidos(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: Usuario = Depends(get_current_admin),
):
    """Carga masiva de pedidos desde un Excel (CUS-13)."""
    contenido = await file.read()  # leemos el archivo subido (bytes)
    return pedido_service.cargar_pedidos_excel(db, contenido, file.filename, usuario_id=admin.id)


@router.get("/", response_model=List[PedidoResponse], dependencies=[Depends(get_current_admin)])
def listar_pedidos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Lista paginada de pedidos."""
    return pedido_service.listar_pedidos(db, skip=skip, limit=limit)


@router.post("/geocodificar", response_model=GeocodificacionResponse)
def procesar_geocodificacion(db: Session = Depends(get_db), admin: Usuario = Depends(get_current_admin)):
    """Convierte las direcciones en coordenadas y deduce el distrito (CUS-15)."""
    return pedido_service.procesar_geocodificacion(db, usuario_id=admin.id)


@router.get("/zonas", response_model=ZonasResponse, dependencies=[Depends(get_current_admin)])
def agrupar_pedidos_por_zona(db: Session = Depends(get_db)):
    """Agrupa los pedidos geocodificados por distrito (CUS-16)."""
    return pedido_service.agrupar_por_zona(db)
