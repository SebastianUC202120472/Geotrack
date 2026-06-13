# app/api/rutas.py
# Expone las URLs de enrutamiento (Fase 2).
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
