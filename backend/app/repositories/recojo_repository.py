# app/repositories/recojo_repository.py
# Única capa que consulta/escribe en la tabla 'solicitudes_recojo'.
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.solicitud_recojo import SolicitudRecojo
from app.models.evidencia_recojo import EvidenciaRecojo
from app.core.codigos import asignar_codigo, PREFIJO_RECOJO


def agregar(db: Session, recojo: SolicitudRecojo) -> SolicitudRecojo:
    """Persiste una solicitud nueva y le asigna el código RC-001 (hace flush -> id)."""
    db.add(recojo)
    asignar_codigo(db, recojo, PREFIJO_RECOJO)
    return recojo


def obtener_por_id(db: Session, recojo_id: int) -> Optional[SolicitudRecojo]:
    """Busca una solicitud por su id. Devuelve None si no existe."""
    return db.query(SolicitudRecojo).filter(SolicitudRecojo.id == recojo_id).first()


def obtener_por_id_bloqueado(db: Session, recojo_id: int) -> Optional[SolicitudRecojo]:
    """Como obtener_por_id pero con bloqueo de fila (SELECT ... FOR UPDATE). Serializa el
    ingreso manual: dos confirmaciones simultáneas del mismo recojo se procesan en orden,
    evitando que ambas lean los pedidos como POR_RECOGER y dupliquen el historial."""
    return (
        db.query(SolicitudRecojo)
        .filter(SolicitudRecojo.id == recojo_id)
        .with_for_update()
        .first()
    )


def obtener_por_ids(db: Session, ids: List[int]) -> List[SolicitudRecojo]:
    """Devuelve las solicitudes cuyos ids están en la lista. Recibe: lista de ids."""
    if not ids:
        return []
    return db.query(SolicitudRecojo).filter(SolicitudRecojo.id.in_(ids)).all()


def listar(db: Session, estado: Optional[str] = None) -> List[SolicitudRecojo]:
    """Lista las solicitudes (filtro opcional por estado), las más nuevas primero."""
    consulta = db.query(SolicitudRecojo)
    if estado:
        consulta = consulta.filter(SolicitudRecojo.estado == estado)
    return consulta.order_by(SolicitudRecojo.fecha_creacion.desc()).all()


def obtener_por_ruta(db: Session, ruta_id: int) -> List[SolicitudRecojo]:
    """Solicitudes de una ruta de recojo, ordenadas por secuencia. Recibe: id de ruta."""
    return (
        db.query(SolicitudRecojo)
        .filter(SolicitudRecojo.ruta_id == ruta_id)
        .order_by(SolicitudRecojo.secuencia.asc())
        .all()
    )


def contar_pendientes_por_ruta(db: Session, ruta_id: int) -> int:
    """Cuántas solicitudes de la ruta NO están recogidas todavía. Recibe: id de ruta."""
    return (
        db.query(SolicitudRecojo)
        .filter(SolicitudRecojo.ruta_id == ruta_id, SolicitudRecojo.estado != "RECOGIDO")
        .count()
    )


def agregar_evidencia(db: Session, recojo_id: int, url_foto: str, secuencia: int) -> EvidenciaRecojo:
    """Registra una foto de evidencia del recojo (no hace commit). Recibe: id del recojo,
    URL servida en /media y el orden de captura."""
    evidencia = EvidenciaRecojo(recojo_id=recojo_id, url_foto=url_foto, secuencia=secuencia)
    db.add(evidencia)
    return evidencia


def guardar_cambios(db: Session) -> None:
    """Confirma en PostgreSQL todos los cambios pendientes de la transacción."""
    db.commit()
