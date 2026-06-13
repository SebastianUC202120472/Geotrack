# app/api/reportes.py
# Reportes de incidencia para el panel del admin: listar y responder.
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_current_admin
from app.models.usuario import Usuario
from app.services import reporte_service
from app.schemas.reporte import ReporteResponse, ResponderReporte

router = APIRouter()


@router.get("/", response_model=List[ReporteResponse], dependencies=[Depends(get_current_admin)])
def listar_reportes(estado: Optional[str] = None, db: Session = Depends(get_db)):
    """Lista los reportes (abiertos primero). Filtra por estado si se indica."""
    return reporte_service.listar(db, estado)


@router.post("/{reporte_id}/responder", response_model=ReporteResponse)
def responder_reporte(
    reporte_id: int,
    datos: ResponderReporte,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(get_current_admin),
):
    """Responde un reporte con la solución y lo marca resuelto."""
    return reporte_service.responder(db, reporte_id, admin.id, datos)
