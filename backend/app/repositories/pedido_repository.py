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


def _filtrar(query, busqueda: Optional[str], distrito: Optional[str], estado: Optional[str]):
    """Aplica a la consulta los filtros opcionales de texto, distrito y estado. Recibe la consulta y los filtros."""
    if busqueda:
        patron = f"%{busqueda}%"
        query = query.filter(
            (Pedido.codigo.ilike(patron)) |
            (Pedido.cliente_origen.ilike(patron)) |
            (Pedido.direccion_destino.ilike(patron)) |
            (Pedido.distrito.ilike(patron))
        )
    if distrito:
        query = query.filter(Pedido.distrito == distrito)
    if estado:
        query = query.filter(Pedido.estado == estado)
    return query


def listar(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    busqueda: Optional[str] = None,
    distrito: Optional[str] = None,
    estado: Optional[str] = None,
) -> List[Pedido]:
    """Devuelve pedidos paginados y filtrados, del mas nuevo al mas antiguo. Recibe offset, limite y filtros."""
    query = _filtrar(db.query(Pedido), busqueda, distrito, estado)
    return query.order_by(Pedido.id.desc()).offset(skip).limit(limit).all()


def contar_activos_por_distrito(db: Session):
    """Cuenta por distrito los pedidos LISTO_PARA_ENVIO y ASIGNADO (zonas por enrutar). Recibe db."""
    return (
        db.query(Pedido.distrito, Pedido.estado, func.count(Pedido.id).label("total"))
        .filter(Pedido.estado.in_(("LISTO_PARA_ENVIO", "ASIGNADO")))
        .group_by(Pedido.distrito, Pedido.estado)
        .all()
    )


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


def referencias_existentes(db: Session, cliente_id: int, referencias: list) -> dict:
    """Pedidos vigentes (no cancelados) de un cliente con esas referencias del retail (C11-01).
    Recibe el id del cliente y la lista de referencias. Devuelve {referencia: codigo PD}."""
    refs = [r for r in {(r or "").strip() for r in referencias} if r]
    if not refs:
        return {}
    filas = (
        db.query(Pedido.referencia_externa, Pedido.codigo)
        .filter(Pedido.cliente_id == cliente_id, Pedido.referencia_externa.in_(refs), Pedido.estado != "CANCELADO")
        .all()
    )
    return {ref: codigo for ref, codigo in filas}


def totales_por_recojo(db: Session, recojo_ids: list) -> dict:
    """Cantidad, volumen y peso de los pedidos de cada recojo en una sola consulta (C12-03).
    Recibe la lista de ids de recojo. Devuelve {recojo_id: (cantidad, volumen_m3, peso_kg)}."""
    from sqlalchemy import func
    if not recojo_ids:
        return {}
    filas = (
        db.query(Pedido.recojo_id, func.count(Pedido.id),
                 func.coalesce(func.sum(Pedido.volumen_m3), 0), func.coalesce(func.sum(Pedido.peso_kg), 0))
        .filter(Pedido.recojo_id.in_(recojo_ids))
        .group_by(Pedido.recojo_id)
        .all()
    )
    return {rid: (int(n), float(vol or 0), float(peso or 0)) for rid, n, vol, peso in filas}


def listar_observados(db: Session) -> list:
    """Pedidos OBSERVADO con su lote (recojo) y desde cuando estan observados (C15-01).
    Devuelve [(pedido, codigo del recojo, fecha en que paso a OBSERVADO)] del mas antiguo al mas nuevo."""
    from sqlalchemy import func
    from app.models.historial import HistorialPedido
    from app.models.solicitud_recojo import SolicitudRecojo
    desde = (
        db.query(HistorialPedido.pedido_id, func.max(HistorialPedido.fecha_utc).label("desde"))
        .filter(HistorialPedido.estado_nuevo == "OBSERVADO")
        .group_by(HistorialPedido.pedido_id)
        .subquery()
    )
    return (
        db.query(Pedido, SolicitudRecojo.codigo, desde.c.desde)
        .outerjoin(SolicitudRecojo, SolicitudRecojo.id == Pedido.recojo_id)
        .outerjoin(desde, desde.c.pedido_id == Pedido.id)
        .filter(Pedido.estado == "OBSERVADO")
        .order_by(desde.c.desde.asc().nullsfirst(), Pedido.id.asc())
        .all()
    )
