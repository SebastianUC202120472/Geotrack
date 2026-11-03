from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.reprogramacion import SolicitudReprogramacion


def pendiente_de(db: Session, pedido_id: int) -> Optional[SolicitudReprogramacion]:
    """Solicitud PENDIENTE del pedido, si hay. Recibe pedido_id."""
    return (
        db.query(SolicitudReprogramacion)
        .filter(SolicitudReprogramacion.pedido_id == pedido_id, SolicitudReprogramacion.estado == "PENDIENTE")
        .order_by(SolicitudReprogramacion.id.desc())
        .first()
    )


def ultima_de(db: Session, pedido_id: int) -> Optional[SolicitudReprogramacion]:
    """Ultima solicitud del pedido (cualquier estado). Recibe pedido_id."""
    return (
        db.query(SolicitudReprogramacion)
        .filter(SolicitudReprogramacion.pedido_id == pedido_id)
        .order_by(SolicitudReprogramacion.id.desc())
        .first()
    )


def listar_de(db: Session, pedido_id: int) -> List[SolicitudReprogramacion]:
    """Solicitudes del pedido, de la mas reciente a la mas antigua. Recibe pedido_id."""
    return (
        db.query(SolicitudReprogramacion)
        .filter(SolicitudReprogramacion.pedido_id == pedido_id)
        .order_by(SolicitudReprogramacion.id.desc())
        .all()
    )


def obtener(db: Session, solicitud_id: int, bloquear: bool = False) -> Optional[SolicitudReprogramacion]:
    """Solicitud por id; con bloquear=True la fila queda tomada hasta el commit. Recibe solicitud_id."""
    consulta = db.query(SolicitudReprogramacion).filter(SolicitudReprogramacion.id == solicitud_id)
    return (consulta.with_for_update() if bloquear else consulta).first()


def registrar(db: Session, pedido_id: int, franja: str) -> SolicitudReprogramacion:
    """Guarda la franja pedida: si ya hay una pendiente la actualiza (no duplica). Sin commit.
    Recibe pedido_id y franja."""
    solicitud = pendiente_de(db, pedido_id)
    if solicitud is None:
        solicitud = SolicitudReprogramacion(pedido_id=pedido_id, franja=franja)
        db.add(solicitud)
    else:
        solicitud.franja = franja
        solicitud.creado_en = datetime.utcnow()
    return solicitud


def atender(solicitud: SolicitudReprogramacion, estado: str, respuesta: Optional[str], usuario_id: Optional[int]) -> None:
    """Marca una solicitud como ACEPTADA o RECHAZADA (sin commit). Recibe la solicitud, estado, nota y admin."""
    solicitud.estado = estado
    solicitud.respuesta = (respuesta or None) and respuesta[:255]
    solicitud.atendida_en = datetime.utcnow()
    solicitud.atendida_por = usuario_id


def cerrar_pendientes(db: Session, pedido_id: int, estado: str, respuesta: str, usuario_id: Optional[int]) -> None:
    """Atiende de una vez las solicitudes pendientes del pedido (al reprogramarlo o cancelarlo). Sin commit.
    Recibe pedido_id, estado final, nota y admin."""
    pendientes = (
        db.query(SolicitudReprogramacion)
        .filter(SolicitudReprogramacion.pedido_id == pedido_id, SolicitudReprogramacion.estado == "PENDIENTE")
        .all()
    )
    for solicitud in pendientes:
        atender(solicitud, estado, respuesta, usuario_id)
