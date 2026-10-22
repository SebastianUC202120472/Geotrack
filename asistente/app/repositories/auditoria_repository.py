from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.auditoria import Auditoria


def registrar(db: Session, **datos) -> Auditoria:
    """Guarda una fila de auditoria. Recibe db y los campos de Auditoria."""
    fila = Auditoria(**datos)
    db.add(fila)
    db.commit()
    return fila


def contar_desde(db: Session, usuario_id: int, desde_utc: datetime) -> int:
    """Cuenta los mensajes del usuario desde una marca UTC (tope diario). Recibe db, usuario_id y desde."""
    return (
        db.query(func.count(Auditoria.id))
        .filter(
            Auditoria.usuario_id == usuario_id,
            Auditoria.creado_en >= desde_utc,
            Auditoria.resultado != "limite",
        )
        .scalar()
        or 0
    )
