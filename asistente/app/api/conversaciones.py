from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.api.deps import obtener_usuario
from app.db.database import get_db
from app.repositories import conversacion_repository
from app.schemas.chat import ConversacionDetalle, ConversacionItem

router = APIRouter()
_ID = Path(pattern=r"^[a-f0-9]{32}$")


@router.get("", response_model=list[ConversacionItem])
def listar(db: Session = Depends(get_db), usuario: dict = Depends(obtener_usuario)):
    """Historial de conversaciones del usuario conectado. Sin input."""
    return conversacion_repository.listar_del_usuario(db, usuario["id"])


@router.get("/{conversacion_id}", response_model=ConversacionDetalle)
def detalle(conversacion_id: str = _ID, db: Session = Depends(get_db), usuario: dict = Depends(obtener_usuario)):
    """Mensajes de una conversacion propia. Recibe su id."""
    conversacion = conversacion_repository.obtener_del_usuario(db, conversacion_id, usuario["id"])
    if not conversacion:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversación no encontrada")
    return conversacion


@router.delete("/{conversacion_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(conversacion_id: str = _ID, db: Session = Depends(get_db), usuario: dict = Depends(obtener_usuario)):
    """Borra una conversacion propia del historial. Recibe su id."""
    conversacion = conversacion_repository.obtener_del_usuario(db, conversacion_id, usuario["id"])
    if not conversacion:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversación no encontrada")
    conversacion_repository.eliminar(db, conversacion)
