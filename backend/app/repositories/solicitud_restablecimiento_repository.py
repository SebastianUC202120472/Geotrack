# app/repositories/solicitud_restablecimiento_repository.py
# Única capa que escribe/lee la tabla 'solicitudes_restablecimiento' (extra CUS-04).
from datetime import datetime
from typing import Set
from sqlalchemy.orm import Session

from app.models.solicitud_restablecimiento import SolicitudRestablecimiento


def crear_o_refrescar(db: Session, conductor_id: int, correo: str) -> SolicitudRestablecimiento:
    """Crea una solicitud PENDIENTE para el conductor; si ya tenía una pendiente, solo
    actualiza su fecha (evita duplicados). Recibe: id del conductor y su correo."""
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
    """Conjunto de conductor_id que tienen una solicitud PENDIENTE (para marcar el
    aviso en la lista de conductores sin consultar uno por uno). Recibe: la sesión."""
    filas = (
        db.query(SolicitudRestablecimiento.conductor_id)
        .filter(SolicitudRestablecimiento.estado == "PENDIENTE")
        .distinct()
        .all()
    )
    return {fila[0] for fila in filas}


def marcar_atendidas(db: Session, conductor_id: int) -> None:
    """Marca como ATENDIDA toda solicitud pendiente del conductor (cuando el admin le
    restablece la contraseña). Recibe: id del conductor."""
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
