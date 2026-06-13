# app/api/correos.py
# Expone la bandeja de solicitudes de recojo.
from typing import List
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_current_admin
from app.models.usuario import Usuario
from app.services import correo_service
from app.schemas.correo import (
    ConversacionResumen,
    ConversacionDetalle,
    ResponderRequest,
    SyncResponse,
)

router = APIRouter()


@router.get("/conversaciones", response_model=List[ConversacionResumen], dependencies=[Depends(get_current_admin)])
def listar_conversaciones(db: Session = Depends(get_db)):
    """Lista los hilos de la bandeja (más recientes primero)."""
    return correo_service.listar(db)


@router.get("/conversaciones/{conversacion_id}", response_model=ConversacionDetalle, dependencies=[Depends(get_current_admin)])
def obtener_conversacion(conversacion_id: int, db: Session = Depends(get_db)):
    """Devuelve un hilo completo y lo marca como leído."""
    return correo_service.obtener_detalle(db, conversacion_id)


@router.post("/sincronizar", response_model=SyncResponse, dependencies=[Depends(get_current_admin)])
def sincronizar(db: Session = Depends(get_db)):
    """Revisa la bandeja por IMAP e importa los correos entrantes nuevos."""
    return correo_service.sincronizar(db)


@router.post("/conversaciones/{conversacion_id}/responder", dependencies=[Depends(get_current_admin)])
def responder(conversacion_id: int, datos: ResponderRequest, db: Session = Depends(get_db), admin: Usuario = Depends(get_current_admin)):
    """Envía una respuesta por SMTP y la guarda en el hilo."""
    return correo_service.responder(db, conversacion_id, datos.cuerpo, admin_id=admin.id)


@router.patch("/conversaciones/{conversacion_id}/estado", response_model=ConversacionResumen, dependencies=[Depends(get_current_admin)])
def cambiar_estado(conversacion_id: int, estado: str, db: Session = Depends(get_db)):
    """Marca la conversación como ATENDIDA o PENDIENTE."""
    return correo_service.cambiar_estado(db, conversacion_id, estado)


@router.get("/adjuntos/{adjunto_id}", dependencies=[Depends(get_current_admin)])
def descargar_adjunto(adjunto_id: int, db: Session = Depends(get_db)):
    """Descarga un adjunto (ej. el Excel del recojo) para subirlo luego en Importar Pedidos."""
    adjunto = correo_service.obtener_adjunto(db, adjunto_id)
    return Response(
        content=adjunto.contenido,
        media_type=adjunto.content_type or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{adjunto.nombre_archivo}"'},
    )
