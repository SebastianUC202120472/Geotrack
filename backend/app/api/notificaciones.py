# app/api/notificaciones.py
# Endpoint del panel admin para obtener los contadores de avisos accionables.
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_current_admin
from app.services import notificaciones_service
from app.schemas.notificacion import NotificacionesResponse

router = APIRouter()


@router.get("", response_model=NotificacionesResponse, dependencies=[Depends(get_current_admin)])
def listar_notificaciones(db: Session = Depends(get_db)):
    """Feed de avisos accionables del admin (contadores por tipo)."""
    return notificaciones_service.obtener(db)
