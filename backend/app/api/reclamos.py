from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_current_admin
from app.repositories import reclamo_repository as repo

router = APIRouter()


@router.get("/", dependencies=[Depends(get_current_admin)])
def listar_reclamos(db: Session = Depends(get_db)):
    """Lista los reclamos del Libro de Reclamaciones (admin)."""
    return [
        {
            "id": r.id, "codigo": r.codigo, "tipo": r.tipo,
            "consumidor": r.consumidor_nombre, "dni": r.consumidor_dni,
            "email": r.consumidor_email, "detalle": r.detalle,
            "pedido": r.pedido_codigo,
            "creado_en": r.creado_en.isoformat() if r.creado_en else None,
        }
        for r in repo.listar_reclamos(db)
    ]
