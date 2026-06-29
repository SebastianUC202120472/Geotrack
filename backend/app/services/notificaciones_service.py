# app/services/notificaciones_service.py
# Lógica de negocio para el historial de notificaciones del panel admin.
from sqlalchemy.orm import Session

from app.models.notificacion import Notificacion


def registrar(db: Session, tipo: str, titulo: str, mensaje: str = None,
              ruta: str = None, entidad_id: int = None) -> Notificacion:
    """Registra una notificación nueva. Best-effort: el llamador la envuelve en try/except.
    Recibe: sesión de BD, tipo, título, mensaje opcional, ruta opcional, id de entidad opcional."""
    n = Notificacion(tipo=tipo, titulo=titulo, mensaje=mensaje,
                     ruta=ruta, entidad_id=entidad_id)
    db.add(n)
    db.flush()
    return n


def listar(db: Session, limite: int = 50) -> dict:
    """Devuelve las últimas notificaciones y el total de no vistas.
    Recibe: sesión de BD, límite de registros a devolver."""
    items = (
        db.query(Notificacion)
        .order_by(Notificacion.creado_en.desc())
        .limit(limite)
        .all()
    )
    no_vistas = (
        db.query(Notificacion)
        .filter(Notificacion.visto_en == None)  # noqa: E711
        .count()
    )
    return {"no_vistas": no_vistas, "items": items}


def marcar_vistas(db: Session) -> int:
    """Marca todas las notificaciones no vistas como vistas; devuelve cuántas se marcaron.
    Recibe: sesión de BD."""
    from datetime import datetime
    n = (
        db.query(Notificacion)
        .filter(Notificacion.visto_en == None)  # noqa: E711
        .update({Notificacion.visto_en: datetime.utcnow()})
    )
    db.commit()
    return n
