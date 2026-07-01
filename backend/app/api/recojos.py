from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Query, UploadFile
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
    """Registra una solicitud de recojo. Recibe datos del admin."""
    return recojo_service.crear_solicitud(db, datos, usuario_id=admin.id)


@router.get("/", response_model=List[SolicitudRecojoResponse])
def listar_recojos(
    estado: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    admin: Usuario = Depends(get_current_admin),
):
    """Lista las solicitudes de recojo. Recibe filtro opcional por estado."""
    return recojo_service.listar_solicitudes(db, estado)


@router.post("/aceptar", response_model=AceptarSolicitudResponse)
async def aceptar_solicitud(
    background_tasks: BackgroundTasks,
    cliente_id: int = Form(...),
    referencia: str | None = Form(None),
    contacto_origen: str | None = Form(None),
    conversacion_id: int | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: Usuario = Depends(get_current_admin),
):
    """Acepta una solicitud: crea pedidos POR_RECOGER desde Excel y geocodifica en segundo plano. Recibe Excel + metadatos del admin."""
    contenido = await file.read()
    resultado = recojo_service.aceptar_solicitud(
        db, cliente_id, contenido, file.filename, referencia, contacto_origen, admin.id, conversacion_id
    )
    background_tasks.add_task(recojo_service.geocodificar_pedidos_recojo, resultado.recojo_id)
    return resultado


@router.get("/{recojo_id}", response_model=SolicitudRecojoResponse)
def obtener_recojo(
    recojo_id: int,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(get_current_admin),
):
    """Devuelve el detalle de una solicitud de recojo. Recibe recojo_id."""
    return recojo_service.obtener_solicitud(db, recojo_id)


@router.patch("/{recojo_id}", response_model=SolicitudRecojoResponse)
def editar_recojo(
    recojo_id: int,
    datos: SolicitudRecojoUpdate,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(get_current_admin),
):
    """Edita una solicitud en estado SOLICITADO. Recibe recojo_id y campos a actualizar."""
    return recojo_service.editar_solicitud(db, recojo_id, datos)
