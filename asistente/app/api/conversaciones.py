from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.api.deps import obtener_usuario
from app.db.database import get_db
from app.repositories import accion_repository, conversacion_repository
from app.schemas.chat import ConversacionDetalle, ConversacionItem

router = APIRouter()
_ID = Path(pattern=r"^[a-f0-9]{32}$")


@router.get("", response_model=list[ConversacionItem])
def listar(db: Session = Depends(get_db), usuario: dict = Depends(obtener_usuario)):
    """Historial de conversaciones del usuario conectado. Sin input."""
    return conversacion_repository.listar_del_usuario(db, usuario["id"])


def _con_estado_de_acciones(db: Session, conversacion, usuario: dict) -> dict:
    """Copia de la conversacion donde cada tarjeta de accion lleva su estado actual (no el de cuando se
    propuso). Recibe db, conversacion y usuario."""
    detalle = ConversacionDetalle.model_validate(conversacion).model_dump()
    ids = [b.get("id") for m in detalle["mensajes"] for b in (m.get("bloques") or []) if b.get("tipo") == "accion"]
    propuestas = accion_repository.estados(db, [i for i in ids if isinstance(i, str)], usuario["id"])
    for propuesta in propuestas.values():
        accion_repository.vencer_si_corresponde(db, propuesta, usuario)
    for mensaje in detalle["mensajes"]:
        for bloque in mensaje.get("bloques") or []:
            propuesta = propuestas.get(bloque.get("id")) if bloque.get("tipo") == "accion" else None
            if propuesta:
                bloque["estado"] = propuesta.estado
                bloque["resultado"] = propuesta.resultado
    return detalle


@router.get("/{conversacion_id}", response_model=ConversacionDetalle)
def detalle(conversacion_id: str = _ID, db: Session = Depends(get_db), usuario: dict = Depends(obtener_usuario)):
    """Mensajes de una conversacion propia. Recibe su id."""
    conversacion = conversacion_repository.obtener_del_usuario(db, conversacion_id, usuario["id"])
    if not conversacion:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversación no encontrada")
    return _con_estado_de_acciones(db, conversacion, usuario)


@router.delete("/{conversacion_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(conversacion_id: str = _ID, db: Session = Depends(get_db), usuario: dict = Depends(obtener_usuario)):
    """Borra una conversacion propia del historial (sus propuestas pendientes quedan sin efecto). Recibe su id."""
    conversacion = conversacion_repository.obtener_del_usuario(db, conversacion_id, usuario["id"])
    if not conversacion:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversación no encontrada")
    accion_repository.cerrar_pendientes(db, usuario, solo_conversacion=conversacion_id)
    conversacion_repository.eliminar(db, conversacion)
