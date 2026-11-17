# Acceso a las tablas de acciones propuestas y derivaciones.
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.fechas import ahora_utc
from app.models.conversacion import Conversacion
from app.models.gestion import Accion, Derivacion


def crear_accion(db: Session, ident: str, conversacion_id: str, tipo: str, resumen: str) -> Accion:
    """Registra una accion propuesta (pendiente). Recibe id, conversacion, tipo y resumen enmascarado."""
    accion = Accion(id=ident, conversacion_id=conversacion_id, tipo=tipo, resumen=resumen[:300])
    db.add(accion)
    db.commit()
    return accion


def obtener_accion(db: Session, ident: str) -> Accion | None:
    """Busca una accion por id. Recibe el id."""
    return db.get(Accion, ident)


def resolver_accion(db: Session, accion: Accion, estado: str, resultado: str | None = None) -> Accion:
    """Cierra una accion con su estado y resultado. Recibe la accion, el estado y el resultado."""
    accion.estado = estado
    accion.resultado = (resultado or "")[:300] or None
    accion.resuelta_en = ahora_utc()
    db.commit()
    return accion


def derivacion_pendiente(db: Session, conversacion_id: str) -> Derivacion | None:
    """Derivacion pendiente de una conversacion, si ya existe. Recibe el id de la conversacion."""
    return db.execute(
        select(Derivacion).where(Derivacion.conversacion_id == conversacion_id, Derivacion.estado == "PENDIENTE")
    ).scalars().first()


def crear_derivacion(db: Session, conversacion: Conversacion, origen: str, motivo: str,
                     contacto: str | None, idioma: str) -> Derivacion:
    """Deja la conversacion en la bandeja y la marca como derivada. Recibe conversacion, origen, motivo,
    contacto (opcional) e idioma."""
    derivacion = Derivacion(conversacion_id=conversacion.id, origen=origen, motivo=motivo[:300],
                            contacto=(contacto or None), idioma=idioma)
    db.add(derivacion)
    conversacion.estado = "DERIVADA"
    db.commit()
    db.refresh(derivacion)
    return derivacion
