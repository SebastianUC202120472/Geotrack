# app/api/recojos.py
# Endpoints del admin para el módulo Inbound de recojos (CUS-10 alta, CUS-11 asignación).
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_current_admin
from app.models.usuario import Usuario
from app.services import recojo_service
from app.schemas.recojo import (
    SolicitudRecojoCreate,
    SolicitudRecojoUpdate,
    SolicitudRecojoResponse,
    AceptarSolicitudResponse,
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


@router.post("/aceptar", response_model=AceptarSolicitudResponse)
async def aceptar_solicitud(
    cliente_id: int = Form(...),
    referencia: str | None = Form(None),
    contacto_origen: str | None = Form(None),
    conversacion_id: int | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: Usuario = Depends(get_current_admin),
):
    """Acepta una solicitud de recojo: crea el recojo y un pedido POR_RECOGER por fila del Excel.
    Si se pasa conversacion_id, enlaza el hilo de correo y lo marca como ATENDIDO."""
    contenido = await file.read()
    return recojo_service.aceptar_solicitud(
        db, cliente_id, contenido, file.filename, referencia, contacto_origen, admin.id, conversacion_id
    )


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
