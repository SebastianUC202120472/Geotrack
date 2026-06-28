# app/repositories/almacen_repository.py
# Acceso a datos del módulo de almacén: pedidos del recojo y desconocidos.
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.pedido import Pedido
from app.models.paquete_esperado import EscaneoDesconocido


def listar_pedidos_recojo(db: Session, recojo_id: int) -> List[Pedido]:
    """Pedidos asociados a un recojo, ordenados por referencia_externa."""
    return (
        db.query(Pedido)
        .filter(Pedido.recojo_id == recojo_id)
        .order_by(Pedido.referencia_externa.asc())
        .all()
    )


def obtener_pedido_por_tracking(db: Session, recojo_id: int, codigo: str) -> Optional[Pedido]:
    """Busca un pedido del recojo por su tracking del cliente (referencia_externa)."""
    return (
        db.query(Pedido)
        .filter(Pedido.recojo_id == recojo_id, Pedido.referencia_externa == codigo)
        .first()
    )


def contar_pedidos(db: Session, recojo_id: int) -> Tuple[int, int, int]:
    """Devuelve (total, validados, faltantes) de pedidos en el recojo.
    Validados = estado distinto de POR_RECOGER; faltantes = POR_RECOGER."""
    total = db.query(Pedido).filter(Pedido.recojo_id == recojo_id).count()
    faltantes = (
        db.query(Pedido)
        .filter(Pedido.recojo_id == recojo_id, Pedido.estado == "POR_RECOGER")
        .count()
    )
    validados = total - faltantes
    return total, validados, faltantes


def contar_desconocidos(db: Session, recojo_id: int) -> int:
    """Cantidad de desconocidos registrados para un recojo."""
    return db.query(EscaneoDesconocido).filter(EscaneoDesconocido.recojo_id == recojo_id).count()


def obtener_desconocido(db: Session, recojo_id: int, codigo: str) -> Optional[EscaneoDesconocido]:
    """Busca un desconocido ya registrado (para no duplicarlo)."""
    return (
        db.query(EscaneoDesconocido)
        .filter(EscaneoDesconocido.recojo_id == recojo_id, EscaneoDesconocido.codigo == codigo)
        .first()
    )


def agregar_desconocido(db: Session, recojo_id: int, codigo: str, usuario_id: int | None) -> EscaneoDesconocido:
    """Registra un código escaneado que no corresponde a ningún pedido del recojo. No hace commit."""
    desconocido = EscaneoDesconocido(recojo_id=recojo_id, codigo=codigo, escaneado_por=usuario_id)
    db.add(desconocido)
    return desconocido


def listar_desconocidos(db: Session, recojo_id: int) -> List[EscaneoDesconocido]:
    """Desconocidos de un recojo, ordenados por código."""
    return (
        db.query(EscaneoDesconocido)
        .filter(EscaneoDesconocido.recojo_id == recojo_id)
        .order_by(EscaneoDesconocido.codigo.asc())
        .all()
    )


def guardar_cambios(db: Session) -> None:
    """Confirma los cambios pendientes en PostgreSQL."""
    db.commit()
