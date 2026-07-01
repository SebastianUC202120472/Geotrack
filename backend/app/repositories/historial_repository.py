from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.historial import HistorialPedido
from app.core.codigos import asignar_codigo, generar_codigo, PREFIJO_HISTORIAL


def registrar(
    db: Session,
    pedido_id: int,
    estado_anterior: Optional[str],
    estado_nuevo: str,
    usuario_id: Optional[int] = None,
) -> HistorialPedido:
    """Registra un evento de cambio de estado del pedido. Recibe pedido_id, estados y usuario opcional. Sin commit."""
    evento = HistorialPedido(
        pedido_id=pedido_id,
        estado_anterior=estado_anterior,
        estado_nuevo=estado_nuevo,
        usuario_id=usuario_id,
    )
    db.add(evento)
    asignar_codigo(db, evento, PREFIJO_HISTORIAL)
    return evento


def registrar_bulk(db: Session, eventos: List[dict]) -> List[HistorialPedido]:
    """Inserta varios eventos de historial en un solo flush. Recibe lista de dicts con pedido_id, estados y usuario_id."""
    if not eventos:
        return []
    objetos = [
        HistorialPedido(
            pedido_id=e["pedido_id"],
            estado_anterior=e.get("estado_anterior"),
            estado_nuevo=e["estado_nuevo"],
            usuario_id=e.get("usuario_id"),
        )
        for e in eventos
    ]
    db.add_all(objetos)
    db.flush()
    for evento in objetos:
        evento.codigo = generar_codigo(PREFIJO_HISTORIAL, evento.id)
    return objetos


def listar_por_pedido(db: Session, pedido_id: int) -> List[HistorialPedido]:
    """Devuelve todos los eventos de un pedido ordenados cronologicamente. Recibe pedido_id."""
    return (
        db.query(HistorialPedido)
        .filter(HistorialPedido.pedido_id == pedido_id)
        .order_by(HistorialPedido.fecha_utc.asc(), HistorialPedido.id.asc())
        .all()
    )
