from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_current_admin
from app.models.usuario import Usuario
from app.schemas.portal import ResponderReclamo
from app.services import reclamo_service

router = APIRouter()


@router.get("/", dependencies=[Depends(get_current_admin)])
def listar_reclamos(db: Session = Depends(get_db)):
    """Lista los reclamos del Libro de Reclamaciones con todos sus datos y el plazo legal (admin)."""
    return reclamo_service.listar(db)


@router.post("/{reclamo_id}/responder")
def responder_reclamo(reclamo_id: int, datos: ResponderReclamo, db: Session = Depends(get_db),
                      admin: Usuario = Depends(get_current_admin)):
    """Registra la respuesta al consumidor y su fecha (C41-02). Recibe reclamo_id y {respuesta}."""
    return reclamo_service.responder(db, reclamo_id, datos.respuesta, admin.id)
