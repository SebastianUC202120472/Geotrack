# app/api/notificaciones.py
# Endpoints del panel admin para consultar y marcar notificaciones.
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_current_admin
from app.services import notificaciones_service
from app.schemas.notificacion import NotificacionesResponse

router = APIRouter()


@router.get("", response_model=NotificacionesResponse, dependencies=[Depends(get_current_admin)])
def listar_notificaciones(db: Session = Depends(get_db)):
    """Historial de notificaciones del admin + contador de no vistas."""
    return notificaciones_service.listar(db)


@router.post("/marcar-vistas", dependencies=[Depends(get_current_admin)])
def marcar_vistas(db: Session = Depends(get_db)):
    """Marca todas las notificaciones como vistas; devuelve cuántas se marcaron."""
    return {"marcadas": notificaciones_service.marcar_vistas(db)}
