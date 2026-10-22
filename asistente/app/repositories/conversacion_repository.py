from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.fechas import ahora_utc
from app.models.conversacion import Conversacion, Mensaje


def crear(db: Session, usuario_id: int, titulo: str) -> Conversacion:
    """Crea una conversacion nueva del usuario. Recibe db, usuario_id y titulo."""
    conversacion = Conversacion(usuario_id=usuario_id, titulo=titulo[:120] or "Nueva conversación")
    db.add(conversacion)
    db.commit()
    db.refresh(conversacion)
    return conversacion


def obtener_del_usuario(db: Session, conversacion_id: str, usuario_id: int) -> Optional[Conversacion]:
    """Devuelve la conversacion solo si pertenece al usuario. Recibe db, id y usuario_id."""
    return (
        db.query(Conversacion)
        .filter(Conversacion.id == conversacion_id, Conversacion.usuario_id == usuario_id)
        .first()
    )


def listar_del_usuario(db: Session, usuario_id: int, limite: int = 30) -> List[Conversacion]:
    """Conversaciones del usuario, la mas reciente primero. Recibe db, usuario_id y limite."""
    return (
        db.query(Conversacion)
        .filter(Conversacion.usuario_id == usuario_id)
        .order_by(Conversacion.actualizada_en.desc())
        .limit(limite)
        .all()
    )


def ultimos_mensajes(db: Session, conversacion_id: str, cantidad: int) -> List[Mensaje]:
    """Ultimos mensajes de una conversacion en orden cronologico. Recibe db, id y cantidad."""
    filas = (
        db.query(Mensaje)
        .filter(Mensaje.conversacion_id == conversacion_id)
        .order_by(Mensaje.id.desc())
        .limit(cantidad)
        .all()
    )
    return list(reversed(filas))


def agregar_mensaje(
    db: Session,
    conversacion: Conversacion,
    rol: str,
    contenido: str,
    origen: str = "texto",
    bloques: list | None = None,
    consultas: list | None = None,
) -> Mensaje:
    """Guarda un mensaje y actualiza la fecha de la conversacion. Recibe db, conversacion y datos del mensaje."""
    mensaje = Mensaje(
        conversacion_id=conversacion.id,
        rol=rol,
        contenido=contenido,
        origen=origen,
        bloques=bloques or None,
        consultas=consultas or None,
    )
    conversacion.actualizada_en = ahora_utc()
    db.add(mensaje)
    db.commit()
    db.refresh(mensaje)
    return mensaje


def eliminar(db: Session, conversacion: Conversacion) -> None:
    """Borra una conversacion con todos sus mensajes. Recibe db y la conversacion."""
    db.delete(conversacion)
    db.commit()
