from datetime import datetime
from typing import List

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.reclamo import Reclamo
from app.models.contacto import ContactoComercial


def formato_codigo(anio: int, correlativo: int) -> str:
    """Formatea el codigo del Libro de Reclamaciones. Recibe anio y correlativo."""
    return f"LR-{anio}-{correlativo:04d}"


def crear_reclamo(db: Session, datos: dict) -> Reclamo:
    """Crea un reclamo con codigo correlativo del anio. Recibe un dict con los campos del modelo."""
    anio = datetime.utcnow().year
    inicio = datetime(anio, 1, 1)
    n = db.query(func.count(Reclamo.id)).filter(Reclamo.creado_en >= inicio).scalar() or 0
    reclamo = Reclamo(codigo=formato_codigo(anio, n + 1), **datos)
    db.add(reclamo)
    db.commit()
    db.refresh(reclamo)
    return reclamo


def crear_contacto(db: Session, datos: dict) -> ContactoComercial:
    """Crea un lead de contacto. Recibe un dict con los campos del modelo."""
    lead = ContactoComercial(**datos)
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


def listar_reclamos(db: Session) -> List[Reclamo]:
    """Lista los reclamos mas recientes primero."""
    return db.query(Reclamo).order_by(Reclamo.id.desc()).all()


def listar_contactos(db: Session) -> List[ContactoComercial]:
    """Lista los leads de contacto mas recientes primero."""
    return db.query(ContactoComercial).order_by(ContactoComercial.id.desc()).all()
