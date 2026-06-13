# app/api/rutas.py
# ============================================================================
# CAPA: API / ROUTER (puerta de entrada HTTP) — Clean Architecture
# ----------------------------------------------------------------------------
# ¿QUÉ HACE?  Expone las URLs de enrutamiento (Fase 2):
#               POST /api/rutas/asignar-bloque      -> admin arma la ruta (CUS-18)
#               POST /api/rutas/conductor/optimizar -> conductor optimiza (CUS-19)
# ¿CÓMO?      Endpoints delgados: validan permisos y delegan al SERVICIO.
# SEGURIDAD:  asignar-bloque -> rol 'admin'; optimizar -> rol 'conductor'.
# ¿CON QUÉ SE CONECTA?
#   - services/ruta_service.py -> lógica de asignación y optimización.
#   - schemas/ruta.py          -> moldes de entrada/salida.
#   - api/deps.py              -> control de acceso por rol.
#   - Lo registra: main.py con el prefijo /api/rutas.
# ============================================================================
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_current_admin, get_current_conductor
from app.models.usuario import Usuario
from app.services import ruta_service
from app.schemas.ruta import (
    AsignacionBloqueRequest,
    AsignacionBloqueResponse,
    OptimizacionRequest,
    OptimizacionResponse,
)

router = APIRouter()


@router.post("/asignar-bloque", response_model=AsignacionBloqueResponse)
def administrador_asigna_bloque(
    asignacion: AsignacionBloqueRequest,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(get_current_admin),
):
    """CUS-18: el administrador asigna un bloque de pedidos de un distrito a un conductor."""
    return ruta_service.asignar_bloque(db, asignacion, usuario_id=admin.id)


@router.post("/conductor/optimizar", response_model=OptimizacionResponse)
def conductor_optimiza_ruta(
    solicitud: OptimizacionRequest,
    db: Session = Depends(get_db),
    conductor: Usuario = Depends(get_current_conductor),
):
    """CUS-19: el conductor optimiza la secuencia de SU ruta desde su posición actual."""
    return ruta_service.optimizar_ruta(db, solicitud, conductor.id)
