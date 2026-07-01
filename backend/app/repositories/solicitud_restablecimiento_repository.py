from datetime import datetime
from typing import Set
from sqlalchemy.orm import Session

from app.models.solicitud_restablecimiento import SolicitudRestablecimiento


def crear_o_refrescar(db: Session, conductor_id: int, correo: str) -> SolicitudRestablecimiento:
    """Crea o refresca la solicitud PENDIENTE del conductor. Recibe: conductor_id, correo."""
    solicitud = (
        db.query(SolicitudRestablecimiento)
        .filter(
            SolicitudRestablecimiento.conductor_id == conductor_id,
            SolicitudRestablecimiento.estado == "PENDIENTE",
        )
        .first()
    )
    if solicitud is None:
        solicitud = SolicitudRestablecimiento(conductor_id=conductor_id, correo=correo)
        db.add(solicitud)
    solicitud.fecha_solicitud = datetime.utcnow()
    db.commit()
    db.refresh(solicitud)
    return solicitud


def ids_pendientes(db: Session) -> Set[int]:
    """Retorna los conductor_id con solicitud PENDIENTE. Recibe: la sesion."""
    filas = (
        db.query(SolicitudRestablecimiento.conductor_id)
        .filter(SolicitudRestablecimiento.estado == "PENDIENTE")
        .distinct()
        .all()
    )
    return {fila[0] for fila in filas}


def marcar_atendidas(db: Session, conductor_id: int) -> None:
    """Marca como ATENDIDAS las solicitudes pendientes del conductor. Recibe: conductor_id."""
    pendientes = (
        db.query(SolicitudRestablecimiento)
        .filter(
            SolicitudRestablecimiento.conductor_id == conductor_id,
            SolicitudRestablecimiento.estado == "PENDIENTE",
        )
        .all()
    )
    for solicitud in pendientes:
        solicitud.estado = "ATENDIDA"
        solicitud.fecha_atencion = datetime.utcnow()
    if pendientes:
        db.commit()
