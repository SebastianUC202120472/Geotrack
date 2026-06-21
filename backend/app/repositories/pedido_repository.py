# app/repositories/pedido_repository.py
# Única capa que consulta/escribe en la tabla 'pedidos'.
from typing import List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.pedido import Pedido


def obtener_por_codigo(db: Session, codigo: str) -> Optional[Pedido]:
    """Busca un pedido por su código legible 'PD-001' (tracking / QR / historial)."""
    return db.query(Pedido).filter(Pedido.codigo == codigo).first()


def obtener_por_referencia_externa(db: Session, referencia: str) -> Optional[Pedido]:
    """Busca un pedido por la referencia que vino en el Excel (para no duplicar)."""
    return db.query(Pedido).filter(Pedido.referencia_externa == referencia).first()


def crear_pedidos(db: Session, pedidos: List[Pedido]) -> None:
    """Inserta una lista de pedidos de una sola vez (carga masiva de Excel)."""
    db.add_all(pedidos)
    db.commit()


def listar(db: Session, skip: int = 0, limit: int = 100) -> List[Pedido]:
    """Devuelve los pedidos paginados (para el panel web del admin)."""
    return db.query(Pedido).offset(skip).limit(limit).all()


def obtener_sin_coordenadas(db: Session) -> List[Pedido]:
    """Pedidos que aún no tienen latitud (faltan por geocodificar)."""
    return db.query(Pedido).filter(Pedido.latitud == None).all()  # noqa: E711 (SQLAlchemy exige '== None')


def obtener_pendientes_por_distrito(db: Session, distrito: str) -> List[Pedido]:
    """Pedidos PENDIENTES de un distrito (base para armar una ruta, CUS-18)."""
    return (
        db.query(Pedido)
        .filter(Pedido.distrito == distrito, Pedido.estado == "PENDIENTE")
        .all()
    )


def agrupar_por_zona(db: Session):
    """Cuenta cuántos pedidos geocodificados hay por distrito (CUS-16)."""
    return (
        db.query(Pedido.distrito, func.count(Pedido.id).label("total_pedidos"))
        .filter(Pedido.latitud != None)  # noqa: E711
        .group_by(Pedido.distrito)
        .all()
    )


def guardar_cambios(db: Session) -> None:
    """Confirma en la BD los cambios hechos sobre pedidos ya cargados (UPDATE)."""
    db.commit()


# --- Fase 4: trazabilidad (CUS-33 / CUS-35) ---
def contar_total(db: Session) -> int:
    """Número total de pedidos en el sistema."""
    return db.query(func.count(Pedido.id)).scalar() or 0


def contar_por_estado(db: Session):
    """Cuenta los pedidos agrupados por su estado (para los KPIs del dashboard)."""
    return (
        db.query(Pedido.estado, func.count(Pedido.id).label("total"))
        .group_by(Pedido.estado)
        .all()
    )


def listar_por_cliente(db: Session, cliente: str, desde=None, hasta=None) -> List[Pedido]:
    """Pedidos de UNA empresa (por su nombre snapshot 'cliente_origen'), para armar la
    liquidación (CUS-36). `desde`/`hasta` (date, opcionales) acotan por fecha_creacion.
    Recibe: nombre del cliente y el rango de fechas. Devuelve la lista de pedidos."""
    from datetime import datetime, time
    consulta = db.query(Pedido).filter(Pedido.cliente_origen == cliente)
    if desde is not None:
        consulta = consulta.filter(Pedido.fecha_creacion >= datetime.combine(desde, time.min))
    if hasta is not None:
        consulta = consulta.filter(Pedido.fecha_creacion <= datetime.combine(hasta, time.max))
    return consulta.order_by(Pedido.codigo.asc()).all()


def agrupar_por_cliente(db: Session):
    """Cuenta pedidos por empresa (cliente_origen) y estado EFECTIVO, para el
    seguimiento por cliente. Si el pedido está en una ruta, su estado real es el del
    detalle (estado_entrega: PENDIENTE/ENTREGADO/FALLIDO); si no, el estado del pedido.
    Así un pedido entregado SÍ cuenta como entregado. Devuelve (cliente_origen, estado, total)."""
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
