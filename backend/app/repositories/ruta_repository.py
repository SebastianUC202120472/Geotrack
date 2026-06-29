# app/repositories/ruta_repository.py
# Única capa que consulta/escribe en las tablas 'rutas' y 'ruta_detalles'.
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.ruta import Ruta, RutaDetalle
from app.models.pedido import Pedido
from app.core.codigos import asignar_codigo, PREFIJO_RUTA, PREFIJO_DETALLE

# Una ruta se considera "activa" mientras no haya sido finalizada (CUS-28).
ESTADOS_RUTA_ACTIVA = ("CREADA", "EN_PROGRESO")


def obtener_ruta_activa_por_conductor(db: Session, conductor_id: int) -> Optional[Ruta]:
    """Devuelve la ruta activa más reciente asignada a un conductor."""
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
    """Devuelve los detalles de una ruta junto a su pedido, ordenados por secuencia."""
    return (
        db.query(RutaDetalle, Pedido)
        .join(Pedido, RutaDetalle.pedido_id == Pedido.id)
        .filter(RutaDetalle.ruta_id == ruta_id)
        .order_by(RutaDetalle.secuencia.asc())
        .all()
    )


def obtener_pedido_por_codigo(db: Session, codigo: str) -> Optional[Pedido]:
    """Busca un pedido por su código legible 'PD-001' (lo que se escanea por QR)."""
    return db.query(Pedido).filter(Pedido.codigo == codigo).first()


def obtener_detalle_de_ruta(
    db: Session, ruta_id: int, pedido_id: int
) -> Optional[RutaDetalle]:
    """Devuelve el RutaDetalle que vincula un pedido con una ruta concreta."""
    return (
        db.query(RutaDetalle)
        .filter(
            RutaDetalle.ruta_id == ruta_id,
            RutaDetalle.pedido_id == pedido_id,
        )
        .first()
    )


# --- Fase 2: creación de rutas (CUS-18) ---
def obtener_ruta_por_id(db: Session, ruta_id: int) -> Optional[Ruta]:
    """Busca una ruta por su id. Devuelve None si no existe."""
    return db.query(Ruta).filter(Ruta.id == ruta_id).first()


def crear_ruta(db: Session, nombre: str, conductor_id: int) -> Ruta:
    """
    Crea una ruta vacía y hace 'flush' para obtener su id YA mismo
    (sin cerrar la transacción), porque enseguida le colgamos los detalles.
    """
    ruta = Ruta(nombre=nombre, conductor_id=conductor_id)
    db.add(ruta)
    asignar_codigo(db, ruta, PREFIJO_RUTA)  # codigo legible RT-001 (hace flush -> id)
    return ruta


def agregar_detalle(db: Session, ruta_id: int, pedido_id: int, secuencia: int = 0) -> RutaDetalle:
    """Cuelga un pedido a una ruta (fila en 'ruta_detalles'). No hace commit."""
    detalle = RutaDetalle(ruta_id=ruta_id, pedido_id=pedido_id, secuencia=secuencia)
    db.add(detalle)
    asignar_codigo(db, detalle, PREFIJO_DETALLE)  # codigo legible RD-001
    return detalle


def guardar_cambios(db: Session) -> None:
    """Confirma en PostgreSQL todos los cambios pendientes de la transacción."""
    db.commit()


# --- Fase 4: trazabilidad y seguimiento (CUS-33 / CUS-35) ---
def listar_rutas(db: Session) -> List[Ruta]:
    """Devuelve TODAS las rutas (para el dashboard de flota), las más nuevas primero."""
    return db.query(Ruta).order_by(Ruta.fecha_creacion.desc()).all()


def mapa_ruta_por_pedidos(db: Session, pedido_ids: List[int]) -> dict:
    """Para enriquecer la lista de pedidos: {pedido_id: (ruta_nombre, conductor_id)}.
    Una sola consulta para todos los pedidos (evita N+1)."""
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
    """Quita un pedido de cualquier ruta (al reabrirlo para reasignarlo)."""
    db.query(RutaDetalle).filter(RutaDetalle.pedido_id == pedido_id).delete(synchronize_session=False)


def obtener_detalle_y_ruta_por_pedido(
    db: Session, pedido_id: int
) -> Optional[Tuple[RutaDetalle, Ruta]]:
    """
    Para el historial de un paquete (CUS-35): devuelve el detalle de ruta de un
    pedido junto con la ruta a la que pertenece. None si el pedido no está en
    ninguna ruta todavía.
    """
    return (
        db.query(RutaDetalle, Ruta)
        .join(Ruta, RutaDetalle.ruta_id == Ruta.id)
        .filter(RutaDetalle.pedido_id == pedido_id)
        .first()
    )


# --- CUS-32: logística inversa (retornos de ruta) ---
def obtener_rutas_con_fallidos(db: Session) -> List[Ruta]:
    """Rutas de ENTREGA con al menos un paquete FALLIDO (candidatas a retorno)."""
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
    """Los paquetes FALLIDO de una ruta junto a su pedido, ordenados por secuencia."""
    return (
        db.query(RutaDetalle, Pedido)
        .join(Pedido, RutaDetalle.pedido_id == Pedido.id)
        .filter(RutaDetalle.ruta_id == ruta_id, RutaDetalle.estado_entrega == "FALLIDO")
        .order_by(RutaDetalle.secuencia.asc())
        .all()
    )


def obtener_fallido_por_codigo(db: Session, ruta_id: int, codigo: str) -> Optional[RutaDetalle]:
    """El RutaDetalle FALLIDO de una ruta cuyo pedido tiene el código escaneado."""
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
    """Devuelve (esperados, retornados) de una ruta: FALLIDO totales y ya retornados."""
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
