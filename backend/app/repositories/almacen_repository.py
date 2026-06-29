# app/repositories/almacen_repository.py
# Acceso a datos del módulo de almacén: pedidos del recojo y sus evidencias.
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.pedido import Pedido
from app.models.evidencia_recojo import EvidenciaRecojo


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


def contar_pedidos(db: Session, recojo_id: int) -> Tuple[int, int, int, int]:
    """Devuelve (total, listos, observados, por_recoger) de pedidos en el recojo:
    listos = LISTO_PARA_ENVIO; observados = OBSERVADO; por_recoger = POR_RECOGER (sin procesar)."""
    base = db.query(Pedido).filter(Pedido.recojo_id == recojo_id)
    total = base.count()
    listos = base.filter(Pedido.estado == "LISTO_PARA_ENVIO").count()
    observados = base.filter(Pedido.estado == "OBSERVADO").count()
    por_recoger = base.filter(Pedido.estado == "POR_RECOGER").count()
    return total, listos, observados, por_recoger


def listar_evidencias(db: Session, recojo_id: int) -> List[EvidenciaRecojo]:
    """Fotos (boleta/guía/bultos) que el conductor subió en la recepción, por secuencia."""
    return (
        db.query(EvidenciaRecojo)
        .filter(EvidenciaRecojo.recojo_id == recojo_id)
        .order_by(EvidenciaRecojo.secuencia.asc(), EvidenciaRecojo.id.asc())
        .all()
    )


def guardar_cambios(db: Session) -> None:
    """Confirma los cambios pendientes en PostgreSQL."""
    db.commit()
