from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.reporte import Reporte


def crear(db: Session, **datos) -> Reporte:
    """Inserta un nuevo reporte en la BD. Recibe campos del modelo como kwargs."""
    reporte = Reporte(**datos)
    db.add(reporte)
    db.commit()
    db.refresh(reporte)
    return reporte


def listar(db: Session, estado: Optional[str] = None) -> List[Reporte]:
    """Devuelve todos los reportes, opcionalmente filtrados por estado. Recibe db y estado opcional."""
    consulta = db.query(Reporte)
    if estado:
        consulta = consulta.filter(Reporte.estado == estado)
    return consulta.order_by(Reporte.estado.asc(), Reporte.creado_en.desc()).all()


def listar_por_conductor(db: Session, conductor_id: int) -> List[Reporte]:
    """Devuelve reportes de un conductor ordenados por fecha. Recibe db y conductor_id."""
    return (
        db.query(Reporte)
        .filter(Reporte.conductor_id == conductor_id)
        .order_by(Reporte.creado_en.desc())
        .all()
    )


def obtener(db: Session, reporte_id: int) -> Optional[Reporte]:
    """Busca un reporte por id. Recibe db y reporte_id."""
    return db.query(Reporte).filter(Reporte.id == reporte_id).first()


def guardar(db: Session) -> None:
    """Confirma la transaccion actual. Recibe db."""
    db.commit()


def contar_abiertos(db: Session) -> int:
    """Cuenta reportes en estado ABIERTO. Recibe db."""
    return db.query(Reporte).filter(Reporte.estado == "ABIERTO").count()


def cerrar_abierto_de_pedido(db: Session, pedido_id: int, accion: str, usuario_id: int | None = None) -> None:
    """Marca como RESUELTO el reporte ABIERTO de un pedido. Recibe pedido_id, accion y usuario_id."""
    from datetime import datetime
    reporte = (
        db.query(Reporte)
        .filter(Reporte.pedido_id == pedido_id, Reporte.estado == "ABIERTO")
        .order_by(Reporte.creado_en.desc())
        .first()
    )
    if reporte:
        reporte.estado = "RESUELTO"
        reporte.accion = accion
        reporte.respondido_en = datetime.utcnow()
        reporte.respondido_por = usuario_id
        db.commit()
