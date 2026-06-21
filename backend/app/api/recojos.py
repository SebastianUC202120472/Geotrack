# app/api/recojos.py
# Endpoints del admin para el módulo Inbound de recojos (CUS-10 alta, CUS-11 asignación).
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_current_admin
from app.models.usuario import Usuario
from app.services import recojo_service
from app.schemas.recojo import (
    SolicitudRecojoCreate,
    SolicitudRecojoUpdate,
    SolicitudRecojoResponse,
    AsignarRutaRecojoRequest,
    AsignarRutaRecojoResponse,
)

router = APIRouter()


@router.post("/", response_model=SolicitudRecojoResponse)
def crear_recojo(
    datos: SolicitudRecojoCreate,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(get_current_admin),
):
    """CUS-10: el admin registra una solicitud de recojo."""
    return recojo_service.crear_solicitud(db, datos, usuario_id=admin.id)


@router.get("/", response_model=List[SolicitudRecojoResponse])
def listar_recojos(
    estado: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    admin: Usuario = Depends(get_current_admin),
):
    """CUS-10: lista las solicitudes de recojo (filtro opcional por estado)."""
    return recojo_service.listar_solicitudes(db, estado)


# CUS-11 va ANTES de /{recojo_id} para que 'asignar-ruta' no se confunda con un id.
@router.post("/asignar-ruta", response_model=AsignarRutaRecojoResponse)
def asignar_ruta_recojo(
    datos: AsignarRutaRecojoRequest,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(get_current_admin),
):
    """CUS-11: crea una ruta de recojo con conductor + vehículo."""
    return recojo_service.asignar_ruta_recojo(db, datos, usuario_id=admin.id)


@router.get("/{recojo_id}", response_model=SolicitudRecojoResponse)
def obtener_recojo(
    recojo_id: int,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(get_current_admin),
):
    """CUS-10: detalle de una solicitud de recojo."""
    return recojo_service.obtener_solicitud(db, recojo_id)


@router.patch("/{recojo_id}", response_model=SolicitudRecojoResponse)
def editar_recojo(
    recojo_id: int,
    datos: SolicitudRecojoUpdate,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(get_current_admin),
):
    """CUS-10: edita una solicitud mientras está SOLICITADO."""
    return recojo_service.editar_solicitud(db, recojo_id, datos)
