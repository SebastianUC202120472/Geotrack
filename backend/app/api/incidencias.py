# app/api/incidencias.py
# Endpoints del PANEL (admin) para gestionar las incidencias de auxilio mecánico (CUS-30).
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_current_admin
from app.models.usuario import Usuario
from app.services import incidencia_service
from app.schemas.incidencia import IncidenciaResponse, MandarAyudaRequest

router = APIRouter()


@router.get("", response_model=List[IncidenciaResponse], dependencies=[Depends(get_current_admin)])
def listar_incidencias(estado: str | None = None, db: Session = Depends(get_db)):
    """CUS-30: lista las incidencias (filtro opcional ?estado=ABIERTA|RESUELTA)."""
    return incidencia_service.listar(db, estado)


@router.get("/contador", dependencies=[Depends(get_current_admin)])
def contador_incidencias(db: Session = Depends(get_db)):
    """CUS-30: cuántas incidencias hay abiertas (para el aviso del panel)."""
    return {"abiertas": incidencia_service.contar_abiertas(db)}


@router.post("/{incidencia_id}/mandar-ayuda", response_model=IncidenciaResponse)
def mandar_ayuda(incidencia_id: int, datos: MandarAyudaRequest, db: Session = Depends(get_db), admin: Usuario = Depends(get_current_admin)):
    """CUS-30: el admin envía ayuda al conductor (tipo + nota). Sella la incidencia con
    "Ayuda enviada" pero NO la resuelve: solo el conductor la cierra al reanudar."""
    return incidencia_service.mandar_ayuda(db, incidencia_id, admin.id, datos.tipo, datos.nota)
