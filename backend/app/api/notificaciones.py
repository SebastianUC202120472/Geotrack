from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_current_admin
from app.services import notificaciones_service
from app.schemas.notificacion import NotificacionesResponse

router = APIRouter()


@router.get("", response_model=NotificacionesResponse, dependencies=[Depends(get_current_admin)])
def listar_notificaciones(limite: int = 50, db: Session = Depends(get_db)):
    """Lista notificaciones del admin con contador de no vistas. Recibe limite (int)."""
    return notificaciones_service.listar(db, limite=max(1, min(limite, 500)))


@router.post("/marcar-vistas", dependencies=[Depends(get_current_admin)])
def marcar_vistas(db: Session = Depends(get_db)):
    """Marca todas las notificaciones como vistas; devuelve cuántas se marcaron."""
    return {"marcadas": notificaciones_service.marcar_vistas(db)}
