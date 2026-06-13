# app/repositories/reporte_repository.py
# Acceso a datos de los reportes de incidencia.
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.reporte import Reporte


def crear(db: Session, **datos) -> Reporte:
    reporte = Reporte(**datos)
    db.add(reporte)
    db.commit()
    db.refresh(reporte)
    return reporte


def listar(db: Session, estado: Optional[str] = None) -> List[Reporte]:
    # Abiertos primero y, dentro de cada grupo, los más recientes arriba.
    consulta = db.query(Reporte)
    if estado:
        consulta = consulta.filter(Reporte.estado == estado)
    return consulta.order_by(Reporte.estado.asc(), Reporte.creado_en.desc()).all()


def listar_por_conductor(db: Session, conductor_id: int) -> List[Reporte]:
    return (
        db.query(Reporte)
        .filter(Reporte.conductor_id == conductor_id)
        .order_by(Reporte.creado_en.desc())
        .all()
    )


def obtener(db: Session, reporte_id: int) -> Optional[Reporte]:
    return db.query(Reporte).filter(Reporte.id == reporte_id).first()


def guardar(db: Session) -> None:
    db.commit()
