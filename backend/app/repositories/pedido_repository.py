from typing import List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.pedido import Pedido


def obtener_por_codigo(db: Session, codigo: str) -> Optional[Pedido]:
    """Busca un pedido por su codigo legible (ej. PD-001). Recibe db y codigo."""
    return db.query(Pedido).filter(Pedido.codigo == codigo).first()


def obtener_por_referencia_externa(db: Session, referencia: str) -> Optional[Pedido]:
    """Busca un pedido por referencia externa del Excel para evitar duplicados."""
    return db.query(Pedido).filter(Pedido.referencia_externa == referencia).first()


def crear_pedidos(db: Session, pedidos: List[Pedido]) -> None:
    """Inserta una lista de pedidos en lote. Recibe db y lista de Pedido."""
    db.add_all(pedidos)
    db.commit()


def listar(db: Session, skip: int = 0, limit: int = 100) -> List[Pedido]:
    """Devuelve pedidos paginados. Recibe db, offset y limite."""
    return db.query(Pedido).offset(skip).limit(limit).all()


def obtener_sin_coordenadas(db: Session) -> List[Pedido]:
    """Devuelve pedidos sin latitud en estado LISTO_PARA_ENVIO o GEOCODIFICACION_FALLIDA."""
    return (
        db.query(Pedido)
        .filter(
            Pedido.latitud == None,  # noqa: E711 (SQLAlchemy exige '== None')
            Pedido.estado.in_(("LISTO_PARA_ENVIO", "GEOCODIFICACION_FALLIDA")),
        )
        .all()
    )


def obtener_por_id(db: Session, pedido_id: int) -> Optional[Pedido]:
    """Busca un pedido por id. Recibe db y pedido_id."""
    return db.query(Pedido).filter(Pedido.id == pedido_id).first()


def listar_geocodificacion_fallida(db: Session) -> List[Pedido]:
    """Devuelve pedidos en estado GEOCODIFICACION_FALLIDA para resolucion manual."""
    return (
        db.query(Pedido)
        .filter(Pedido.estado == "GEOCODIFICACION_FALLIDA")
        .order_by(Pedido.codigo.asc())
        .all()
    )


def listar_sin_ubicacion_resoluble(db: Session) -> List[Pedido]:
    """Pedidos sin coordenadas en estados resolubles por el admin, ordenados por codigo."""
    estados_resolubles = ("LISTO_PARA_ENVIO", "POR_RECOGER", "GEOCODIFICACION_FALLIDA")
    return (
        db.query(Pedido)
        .filter(Pedido.latitud == None, Pedido.estado.in_(estados_resolubles))  # noqa: E711
        .order_by(Pedido.codigo.asc())
        .all()
    )


def obtener_pendientes_por_distrito(db: Session, distrito: str) -> List[Pedido]:
    """Devuelve pedidos LISTO_PARA_ENVIO de un distrito. Recibe db y distrito."""
    return (
        db.query(Pedido)
        .filter(Pedido.distrito == distrito, Pedido.estado == "LISTO_PARA_ENVIO")
        .all()
    )


def agrupar_por_zona(db: Session):
    """Cuenta pedidos LISTO_PARA_ENVIO geocodificados agrupados por distrito."""
    return (
        db.query(Pedido.distrito, func.count(Pedido.id).label("total_pedidos"))
        .filter(Pedido.latitud != None, Pedido.estado == "LISTO_PARA_ENVIO")  # noqa: E711
        .group_by(Pedido.distrito)
        .all()
    )


def guardar_cambios(db: Session) -> None:
    """Confirma en BD los cambios pendientes sobre pedidos."""
    db.commit()


def contar_total(db: Session) -> int:
    """Retorna el total de pedidos en el sistema."""
    return db.query(func.count(Pedido.id)).scalar() or 0


def contar_por_estado(db: Session):
    """Cuenta pedidos agrupados por estado para los KPIs del dashboard."""
    return (
        db.query(Pedido.estado, func.count(Pedido.id).label("total"))
        .group_by(Pedido.estado)
        .all()
    )


def listar_por_cliente(db: Session, cliente: str, desde=None, hasta=None, estados=None) -> List[Pedido]:
    """Pedidos de un cliente filtrados por rango de fechas y estados. Recibe db, cliente, desde, hasta y estados."""
    from datetime import datetime, time
    consulta = db.query(Pedido).filter(Pedido.cliente_origen == cliente)
    if estados:
        consulta = consulta.filter(Pedido.estado.in_(tuple(estados)))
    if desde is not None:
        consulta = consulta.filter(Pedido.fecha_creacion >= datetime.combine(desde, time.min))
    if hasta is not None:
        consulta = consulta.filter(Pedido.fecha_creacion <= datetime.combine(hasta, time.max))
    return consulta.order_by(Pedido.codigo.asc()).all()


def agrupar_por_cliente(db: Session):
    """Cuenta pedidos por cliente y estado efectivo (usa estado_entrega del detalle si existe)."""
    from app.models.ruta import RutaDetalle
    estado_efectivo = func.coalesce(RutaDetalle.estado_entrega, Pedido.estado)
    return (
        db.query(
            Pedido.cliente_origen,
            estado_efectivo.label("estado"),
            func.count(func.distinct(Pedido.id)).label("total"),
        )
        .outerjoin(RutaDetalle, RutaDetalle.pedido_id == Pedido.id)
        .group_by(Pedido.cliente_origen, estado_efectivo)
        .all()
    )
