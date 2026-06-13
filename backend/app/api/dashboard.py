# app/api/dashboard.py
# ============================================================================
# CAPA: API / ROUTER (puerta de entrada HTTP) — Clean Architecture
# ----------------------------------------------------------------------------
# ¿QUÉ HACE?  Expone el módulo de TRAZABILIDAD para el panel web del admin (Fase 4):
#               GET /api/dashboard/resumen                      -> KPIs (CUS-33)
#               GET /api/dashboard/flota                        -> avance de rutas (CUS-33)
#               GET /api/dashboard/pedidos/{tracking}/historial -> línea de tiempo (CUS-35)
# ¿CÓMO?      Endpoints delgados que delegan en services/dashboard_service.py.
# SEGURIDAD:  TODOS exigen rol 'admin' (Depends(get_current_admin)).
# ¿CON QUÉ SE CONECTA?
#   - services/dashboard_service.py -> la lógica real.
#   - schemas/dashboard.py          -> moldes de respuesta.
#   - api/deps.py                   -> control de acceso por rol.
#   - Lo registra: main.py con el prefijo /api/dashboard.
# ============================================================================
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_current_admin
from app.services import dashboard_service
from app.schemas.dashboard import FlotaResponse, ResumenResponse, HistorialPedidoResponse

router = APIRouter()


@router.get("/resumen", response_model=ResumenResponse, dependencies=[Depends(get_current_admin)])
def obtener_resumen(db: Session = Depends(get_db)):
    """CUS-33: KPIs globales (pedidos por estado y conteo de rutas)."""
    return dashboard_service.obtener_resumen(db)


@router.get("/flota", response_model=FlotaResponse, dependencies=[Depends(get_current_admin)])
def obtener_flota(db: Session = Depends(get_db)):
    """CUS-33: estado y avance (%) de todas las rutas de la flota."""
    return dashboard_service.obtener_flota(db)


@router.get(
    "/pedidos/{codigo}/historial",
    response_model=HistorialPedidoResponse,
    dependencies=[Depends(get_current_admin)],
)
def obtener_historial(codigo: str, db: Session = Depends(get_db)):
    """CUS-35: línea de tiempo completa de un paquete (por su código PD-001)."""
    return dashboard_service.obtener_historial(db, codigo)
