from datetime import datetime, time
from typing import Optional, List, Tuple

from sqlalchemy.orm import Session

from app.models.pedido import Pedido
from app.models.ruta import Ruta, RutaDetalle
from app.models.usuario import Usuario
from app.models.historial import HistorialPedido
from app.models.evidencia import EvidenciaEntrega
from app.models.cliente import ClienteCorporativo


def pedido_por_codigo(db: Session, codigo: str) -> Optional[Pedido]:
    """Busca un pedido por su codigo. Recibe db y codigo."""
    return db.query(Pedido).filter(Pedido.codigo == codigo).first()


def ruta_y_detalle_de(db: Session, pedido_id: int) -> Tuple[Optional[Ruta], Optional[RutaDetalle], int]:
    """Devuelve (ruta de entrega mas reciente del pedido, su detalle, total de paradas). Recibe pedido_id."""
    detalle = (
        db.query(RutaDetalle)
        .join(Ruta, Ruta.id == RutaDetalle.ruta_id)
        .filter(RutaDetalle.pedido_id == pedido_id, Ruta.tipo == "ENTREGA")
        .order_by(RutaDetalle.id.desc())
        .first()
    )
    if not detalle:
        return None, None, 0
    ruta = db.query(Ruta).filter(Ruta.id == detalle.ruta_id).first()
    total = db.query(RutaDetalle).filter(RutaDetalle.ruta_id == detalle.ruta_id).count()
    return ruta, detalle, total


def conductor_de_ruta(db: Session, conductor_id) -> Optional[Usuario]:
    """Devuelve el usuario conductor de una ruta. Recibe el conductor_id (puede ser None)."""
    if not conductor_id:
        return None
    return db.query(Usuario).filter(Usuario.id == conductor_id).first()


def historial_de(db: Session, pedido_id: int) -> List[HistorialPedido]:
    """Devuelve el historial de un pedido en orden cronologico. Recibe pedido_id."""
    return (
        db.query(HistorialPedido)
        .filter(HistorialPedido.pedido_id == pedido_id)
        .order_by(HistorialPedido.fecha_utc.asc())
        .all()
    )


def evidencia_de(db: Session, pedido_id: int) -> Optional[EvidenciaEntrega]:
    """Devuelve la evidencia de entrega (POD) mas reciente del pedido. Recibe pedido_id."""
    return (
        db.query(EvidenciaEntrega)
        .filter(EvidenciaEntrega.pedido_id == pedido_id)
        .order_by(EvidenciaEntrega.id.desc())
        .first()
    )


def cliente_por_codigo_acceso(db: Session, codigo_acceso: str) -> Optional[ClienteCorporativo]:
    """Busca un cliente corporativo por su codigo de acceso al portal. Recibe codigo_acceso."""
    return (
        db.query(ClienteCorporativo)
        .filter(ClienteCorporativo.codigo_acceso == codigo_acceso)
        .first()
    )


def pedidos_de_cliente_hoy(db: Session, cliente_id: int):
    """Devuelve (pedido, detalle de ruta) del cliente creados hoy. Recibe el id del cliente.
    Filtra por cliente_id (FK) y NO por razon_social, que no es unica (evita fuga cross-empresa)."""
    hoy = datetime.utcnow().date()
    inicio = datetime.combine(hoy, time.min)
    fin = datetime.combine(hoy, time.max)
    pedidos = (
        db.query(Pedido)
        .filter(Pedido.cliente_id == cliente_id, Pedido.fecha_creacion >= inicio, Pedido.fecha_creacion <= fin)
        .order_by(Pedido.codigo.asc())
        .all()
    )
    salida = []
    for p in pedidos:
        det = (
            db.query(RutaDetalle)
            .join(Ruta, Ruta.id == RutaDetalle.ruta_id)
            .filter(RutaDetalle.pedido_id == p.id, Ruta.tipo == "ENTREGA")
            .order_by(RutaDetalle.id.desc())
            .first()
        )
        salida.append((p, det))
    return salida


def conteos_del_dia_reciente(db: Session):
    """Conteos de pedidos por estado del dia MAS RECIENTE con pedidos (normalmente hoy).
    Sin datos personales: solo agregados. Devuelve lista de (estado, total)."""
    from sqlalchemy import func
    ultimo_dia = db.query(func.date(Pedido.fecha_creacion)).order_by(Pedido.fecha_creacion.desc()).limit(1).scalar()
    if ultimo_dia is None:
        return []
    return (
        db.query(Pedido.estado, func.count(Pedido.id))
        .filter(func.date(Pedido.fecha_creacion) == ultimo_dia)
        .group_by(Pedido.estado)
        .all()
    )


def ultimo_pedido(db: Session) -> Optional[Pedido]:
    """Devuelve el pedido mas reciente del sistema (para la tarjeta del landing)."""
    return db.query(Pedido).order_by(Pedido.id.desc()).first()
