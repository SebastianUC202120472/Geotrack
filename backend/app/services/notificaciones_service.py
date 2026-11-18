from datetime import datetime

from sqlalchemy.orm import Session

from app.models.notificacion import Notificacion


def registrar(db: Session, tipo: str, titulo: str, mensaje: str = None,
              ruta: str = None, entidad_id: int = None) -> Notificacion:
    """Registra una notificación best-effort; si falla revierte y devuelve None. Recibe sesión de BD, tipo, título y campos opcionales."""
    try:
        n = Notificacion(tipo=tipo, titulo=titulo, mensaje=mensaje,
                         ruta=ruta, entidad_id=entidad_id)
        db.add(n)
        db.commit()
        db.refresh(n)
        return n
    except Exception:
        db.rollback()
        return None


def registrar_o_actualizar(db: Session, tipo: str, titulo: str, mensaje: str = None,
                           ruta: str = None, entidad_id: int = None) -> Notificacion:
    """Como registrar, pero si ya hay un aviso SIN VER del mismo tipo, titulo y entidad, lo actualiza
    (mensaje y hora) en vez de crear otro: asi un mismo caso no llena la campana. Best-effort.
    Recibe sesión de BD, tipo, título y campos opcionales."""
    try:
        n = (
            db.query(Notificacion)
            .filter(Notificacion.tipo == tipo, Notificacion.titulo == titulo,
                    Notificacion.entidad_id == entidad_id, Notificacion.visto_en == None)  # noqa: E711
            .order_by(Notificacion.id.desc())
            .first()
        )
    except Exception:
        db.rollback()
        return None
    if n is None:
        return registrar(db, tipo, titulo, mensaje, ruta, entidad_id)
    try:
        n.mensaje, n.ruta, n.creado_en = mensaje, ruta, datetime.utcnow()
        db.commit()
        db.refresh(n)
        return n
    except Exception:
        db.rollback()
        return None


def listar(db: Session, limite: int = 50) -> dict:
    """Devuelve las últimas notificaciones y el total de no vistas. Recibe sesión de BD y límite."""
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
    """Marca todas las notificaciones no vistas como vistas y devuelve cuántas. Recibe sesión de BD."""
    from datetime import datetime
    n = (
        db.query(Notificacion)
        .filter(Notificacion.visto_en == None)  # noqa: E711
        .update({Notificacion.visto_en: datetime.utcnow()})
    )
    db.commit()
    return n
