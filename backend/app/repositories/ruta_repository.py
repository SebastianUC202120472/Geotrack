from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.ruta import Ruta, RutaDetalle
from app.models.pedido import Pedido
from app.core.codigos import asignar_codigo, PREFIJO_RUTA, PREFIJO_DETALLE

ESTADOS_RUTA_ACTIVA = ("CREADA", "EN_PROGRESO")


def obtener_ruta_activa_por_conductor(db: Session, conductor_id: int) -> Optional[Ruta]:
    """Ruta activa mas reciente del conductor. Recibe conductor_id."""
    return (
        db.query(Ruta)
        .filter(
            Ruta.conductor_id == conductor_id,
            Ruta.estado.in_(ESTADOS_RUTA_ACTIVA),
        )
        .order_by(Ruta.fecha_creacion.desc())
        .first()
    )


def obtener_detalles_con_pedido(
    db: Session, ruta_id: int
) -> List[Tuple[RutaDetalle, Pedido]]:
    """Detalles de una ruta con su pedido, ordenados por secuencia. Recibe ruta_id."""
    return (
        db.query(RutaDetalle, Pedido)
        .join(Pedido, RutaDetalle.pedido_id == Pedido.id)
        .filter(RutaDetalle.ruta_id == ruta_id)
        .order_by(RutaDetalle.secuencia.asc())
        .all()
    )


def obtener_pedido_por_codigo(db: Session, codigo: str) -> Optional[Pedido]:
    """Busca un pedido por su codigo legible (PD-001). Recibe codigo."""
    return db.query(Pedido).filter(Pedido.codigo == codigo).first()


def obtener_detalle_de_ruta(
    db: Session, ruta_id: int, pedido_id: int
) -> Optional[RutaDetalle]:
    """Vinculo RutaDetalle entre un pedido y una ruta. Recibe ruta_id y pedido_id."""
    return (
        db.query(RutaDetalle)
        .filter(
            RutaDetalle.ruta_id == ruta_id,
            RutaDetalle.pedido_id == pedido_id,
        )
        .first()
    )


def obtener_ruta_por_id(db: Session, ruta_id: int) -> Optional[Ruta]:
    """Busca una ruta por su id. Recibe ruta_id."""
    return db.query(Ruta).filter(Ruta.id == ruta_id).first()


def crear_ruta(db: Session, nombre: str, conductor_id: int) -> Ruta:
    """Crea una ruta vacia con flush para obtener su id antes del commit. Recibe nombre y conductor_id."""
    ruta = Ruta(nombre=nombre, conductor_id=conductor_id)
    db.add(ruta)
    asignar_codigo(db, ruta, PREFIJO_RUTA)
    return ruta


def agregar_detalle(db: Session, ruta_id: int, pedido_id: int, secuencia: int = 0) -> RutaDetalle:
    """Cuelga un pedido a una ruta (fila en 'ruta_detalles'). No hace commit."""
    detalle = RutaDetalle(ruta_id=ruta_id, pedido_id=pedido_id, secuencia=secuencia)
    db.add(detalle)
    asignar_codigo(db, detalle, PREFIJO_DETALLE)
    return detalle


def guardar_cambios(db: Session) -> None:
    """Hace commit de todos los cambios pendientes."""
    db.commit()


def listar_rutas(db: Session) -> List[Ruta]:
    """Devuelve todas las rutas ordenadas por fecha descendente."""
    return db.query(Ruta).order_by(Ruta.fecha_creacion.desc()).all()


def mapa_ruta_por_pedidos(db: Session, pedido_ids: List[int]) -> dict:
    """Devuelve {pedido_id: (ruta_nombre, conductor_id)} en una sola consulta. Recibe lista de ids."""
    if not pedido_ids:
        return {}
    filas = (
        db.query(RutaDetalle.pedido_id, Ruta.nombre, Ruta.conductor_id)
        .join(Ruta, RutaDetalle.ruta_id == Ruta.id)
        .filter(RutaDetalle.pedido_id.in_(pedido_ids))
        .all()
    )
    return {pid: (nombre, conductor_id) for pid, nombre, conductor_id in filas}


def eliminar_detalles_de_pedido(db: Session, pedido_id: int) -> None:
    """Elimina el pedido de cualquier ruta. Recibe pedido_id."""
    db.query(RutaDetalle).filter(RutaDetalle.pedido_id == pedido_id).delete(synchronize_session=False)


def obtener_detalle_y_ruta_por_pedido(
    db: Session, pedido_id: int
) -> Optional[Tuple[RutaDetalle, Ruta]]:
    """Detalle y ruta del pedido. Recibe pedido_id. Devuelve None si no esta en ninguna ruta."""
    return (
        db.query(RutaDetalle, Ruta)
        .join(Ruta, RutaDetalle.ruta_id == Ruta.id)
        .filter(RutaDetalle.pedido_id == pedido_id)
        .first()
    )


def obtener_rutas_con_fallidos(db: Session) -> List[Ruta]:
    """Rutas de ENTREGA con al menos un paquete FALLIDO."""
    ids = (
        db.query(RutaDetalle.ruta_id)
        .filter(RutaDetalle.estado_entrega == "FALLIDO")
        .distinct()
    )
    return (
        db.query(Ruta)
        .filter(Ruta.id.in_(ids), Ruta.tipo == "ENTREGA")
        .order_by(Ruta.fecha_creacion.desc())
        .all()
    )


def obtener_fallidos_de_ruta(db: Session, ruta_id: int) -> List[Tuple[RutaDetalle, Pedido]]:
    """Paquetes FALLIDO de una ruta con su pedido, ordenados por secuencia. Recibe ruta_id."""
    return (
        db.query(RutaDetalle, Pedido)
        .join(Pedido, RutaDetalle.pedido_id == Pedido.id)
        .filter(RutaDetalle.ruta_id == ruta_id, RutaDetalle.estado_entrega == "FALLIDO")
        .order_by(RutaDetalle.secuencia.asc())
        .all()
    )


def obtener_fallido_por_codigo(db: Session, ruta_id: int, codigo: str) -> Optional[RutaDetalle]:
    """RutaDetalle FALLIDO de la ruta cuyo pedido coincide con el codigo. Recibe ruta_id y codigo."""
    return (
        db.query(RutaDetalle)
        .join(Pedido, RutaDetalle.pedido_id == Pedido.id)
        .filter(
            RutaDetalle.ruta_id == ruta_id,
            RutaDetalle.estado_entrega == "FALLIDO",
            Pedido.codigo == codigo,
        )
        .first()
    )


def contar_retorno(db: Session, ruta_id: int) -> Tuple[int, int]:
    """Devuelve (fallidos_totales, ya_retornados) de una ruta. Recibe ruta_id."""
    esperados = (
        db.query(RutaDetalle)
        .filter(RutaDetalle.ruta_id == ruta_id, RutaDetalle.estado_entrega == "FALLIDO")
        .count()
    )
    retornados = (
        db.query(RutaDetalle)
        .filter(
            RutaDetalle.ruta_id == ruta_id,
            RutaDetalle.estado_entrega == "FALLIDO",
            RutaDetalle.retornado_en.isnot(None),
        )
        .count()
    )
    return esperados, retornados
