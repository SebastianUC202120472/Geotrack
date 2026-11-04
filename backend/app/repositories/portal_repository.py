from typing import Optional, List, Tuple

from sqlalchemy.orm import Session

from app.core import fechas
from app.models.pedido import Pedido
from app.models.ruta import Ruta, RutaDetalle
from app.models.usuario import Usuario
from app.models.conductor import PerfilConductor
from app.models.historial import HistorialPedido
from app.models.evidencia import EvidenciaEntrega
from app.models.cliente import ClienteCorporativo
from app.models.parametro import ParametroSistema


def pedido_por_codigo(db: Session, codigo: str) -> Optional[Pedido]:
    """Busca un pedido por su codigo interno (PD-014) o por la referencia del retail
    (RPL-1000). Recibe db y el codigo tecleado por el cliente.
    El destinatario final conoce el numero que le dio la tienda, no el codigo interno
    de SAVA, asi que el portal acepta los dos. Se prioriza el codigo interno para que
    una referencia externa que coincida con un codigo nunca tape al pedido correcto."""
    if not codigo:
        return None
    p = db.query(Pedido).filter(Pedido.codigo == codigo).first()
    if p:
        return p
    return db.query(Pedido).filter(Pedido.referencia_externa == codigo).first()


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


def perfil_conductor(db: Session, usuario_id) -> Optional[PerfilConductor]:
    """Devuelve el perfil (datos personales) de un conductor. Recibe el usuario_id (puede ser None)."""
    if not usuario_id:
        return None
    return db.query(PerfilConductor).filter(PerfilConductor.usuario_id == usuario_id).first()


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


# Estados en curso: un pedido asi sigue "vivo" para el cliente aunque se haya creado otro dia.
ESTADOS_ACTIVOS = ("POR_RECOGER", "OBSERVADO", "LISTO_PARA_ENVIO", "ASIGNADO", "EN_RUTA", "FALLIDO")


def pedidos_de_cliente_en_fecha(db: Session, cliente_id: int, dia=None):
    """Devuelve (pedido, detalle de ruta) de los pedidos del cliente que importan ese dia (C45-01):
    creados ese dia, con algun movimiento ese dia o entregados ese dia; si el dia es hoy, ademas
    todos los que siguen en curso. Recibe el id del cliente y la fecha local (por defecto hoy).
    Filtra por cliente_id (FK) y NO por razon_social, que no es unica (evita fuga cross-empresa).
    El dia es el de la zona horaria de la operacion, no el dia UTC."""
    from sqlalchemy import or_
    dia = dia or fechas.hoy_local()
    inicio, fin = fechas.rango_utc_del_dia(dia)
    con_movimiento = (
        db.query(HistorialPedido.pedido_id)
        .filter(HistorialPedido.fecha_utc >= inicio, HistorialPedido.fecha_utc <= fin)
    )
    condiciones = [
        Pedido.fecha_creacion.between(inicio, fin),
        Pedido.fecha_entrega.between(inicio, fin),
        Pedido.id.in_(con_movimiento),
    ]
    if dia == fechas.hoy_local():
        condiciones.append(Pedido.estado.in_(ESTADOS_ACTIVOS))
    pedidos = (
        db.query(Pedido)
        .filter(Pedido.cliente_id == cliente_id, or_(*condiciones))
        .order_by(Pedido.codigo.asc())
        .all()
    )
    return [(p, _detalle_entrega(db, p.id)) for p in pedidos]


def historial_de_pedidos(db: Session, pedido_ids: List[int]) -> dict:
    """Historial de varios pedidos en una sola consulta, agrupado por pedido y en orden cronologico.
    Recibe la lista de ids. Devuelve {pedido_id: [HistorialPedido, ...]}."""
    if not pedido_ids:
        return {}
    filas = (
        db.query(HistorialPedido)
        .filter(HistorialPedido.pedido_id.in_(pedido_ids))
        .order_by(HistorialPedido.pedido_id.asc(), HistorialPedido.fecha_utc.asc())
        .all()
    )
    agrupado = {}
    for h in filas:
        agrupado.setdefault(h.pedido_id, []).append(h)
    return agrupado


def _detalle_entrega(db: Session, pedido_id: int) -> Optional[RutaDetalle]:
    """Ultimo detalle de una ruta de ENTREGA del pedido (o None). Recibe db y el id del pedido."""
    return (
        db.query(RutaDetalle)
        .join(Ruta, Ruta.id == RutaDetalle.ruta_id)
        .filter(RutaDetalle.pedido_id == pedido_id, Ruta.tipo == "ENTREGA")
        .order_by(RutaDetalle.id.desc())
        .first()
    )


def pedidos_de_clientes(db: Session, cliente_ids: List[int]):
    """Devuelve (pedido, detalle de ruta) de todos los pedidos de esos clientes, por codigo.
    Recibe db y la lista de ids de cliente. Lo usa la ayuda en vivo de la demostracion."""
    if not cliente_ids:
        return []
    pedidos = (
        db.query(Pedido)
        .filter(Pedido.cliente_id.in_(cliente_ids))
        .order_by(Pedido.codigo.asc())
        .all()
    )
    return [(p, _detalle_entrega(db, p.id)) for p in pedidos]


def conteos_del_dia_reciente(db: Session):
    """Conteos por estado del dia operativo MAS RECIENTE con pedidos. Recibe la sesion.
    Devuelve (fecha local del dia, [(estado, total)]). El dia se calcula en la zona de la
    operacion, no en UTC, y se devuelve para que el landing pueda decir si es hoy o no."""
    from sqlalchemy import func
    # isnot(None): un pedido sin fecha (insercion manual) no debe volcar el reporte a
    # vacio (en Postgres los NULL van primero en un ORDER BY DESC).
    ultimo = (
        db.query(Pedido.fecha_creacion)
        .filter(Pedido.fecha_creacion.isnot(None))
        .order_by(Pedido.fecha_creacion.desc())
        .limit(1)
        .scalar()
    )
    if ultimo is None:
        return None, []
    dia = fechas.fecha_local_de(ultimo)
    inicio, fin = fechas.rango_utc_del_dia(dia)
    conteos = (
        db.query(Pedido.estado, func.count(Pedido.id))
        .filter(Pedido.fecha_creacion >= inicio, Pedido.fecha_creacion <= fin)
        .group_by(Pedido.estado)
        .all()
    )
    return dia, conteos


def ultimo_pedido(db: Session) -> Optional[Pedido]:
    """Devuelve el pedido mas reciente del sistema (para la tarjeta del landing)."""
    return db.query(Pedido).order_by(Pedido.id.desc()).first()


def ayuda_demo(db: Session) -> Optional[dict]:
    """Devuelve los datos de ayuda de la demostracion guardados por el seeder. Recibe db.
    None si nunca se sembro la demostracion."""
    fila = (
        db.query(ParametroSistema)
        .filter(ParametroSistema.categoria == "portal_demo", ParametroSistema.clave == "ayuda")
        .first()
    )
    return fila.valor_json if fila else None
