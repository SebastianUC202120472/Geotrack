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


def pedidos_de_cliente_hoy(db: Session, cliente_id: int):
    """Devuelve (pedido, detalle de ruta) del cliente creados hoy. Recibe el id del cliente.
    Filtra por cliente_id (FK) y NO por razon_social, que no es unica (evita fuga cross-empresa).
    "Hoy" es el dia de la zona horaria de la operacion, no el dia UTC: con UTC el dia del
    cliente cambiaria a las 7 p.m. hora de Lima."""
    inicio, fin = fechas.rango_utc_del_dia()
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
