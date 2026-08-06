from typing import Optional

from sqlalchemy.orm import Session

from app.models.verificacion_portal import VerificacionPortal


def obtener(db: Session, tipo: str, referencia: str) -> Optional[VerificacionPortal]:
    """Devuelve el reto vigente de (tipo, referencia) si existe. Recibe tipo y referencia."""
    return (
        db.query(VerificacionPortal)
        .filter(VerificacionPortal.tipo == tipo, VerificacionPortal.referencia == referencia)
        .order_by(VerificacionPortal.id.desc())
        .first()
    )


def upsert(db: Session, tipo: str, referencia: str, **campos) -> VerificacionPortal:
    """Crea o actualiza el reto de (tipo, referencia) con los campos dados. Recibe tipo, referencia y campos."""
    reg = obtener(db, tipo, referencia)
    if reg is None:
        reg = VerificacionPortal(tipo=tipo, referencia=referencia)
        db.add(reg)
    for k, v in campos.items():
        setattr(reg, k, v)
    return reg


def guardar(db: Session) -> None:
    """Confirma los cambios de verificacion en BD."""
    db.commit()
