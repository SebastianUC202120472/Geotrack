# app/repositories/historial_repository.py
# ============================================================================
# CAPA: REPOSITORIO (acceso a datos) — Clean Architecture
# ----------------------------------------------------------------------------
# ¿QUÉ HACE?  Única capa que escribe/lee la tabla 'historial_pedidos' (eventos).
# ¿CON QUÉ SE CONECTA?
#   - models/historial.py -> la tabla de eventos.
#   - Lo USAN: pedido_service.py y ruta_service.py (registran cada cambio) y
#              dashboard_service.py (lee la línea de tiempo para CUS-35).
# ============================================================================
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.historial import HistorialPedido
from app.core.codigos import asignar_codigo, PREFIJO_HISTORIAL


def registrar(
    db: Session,
    pedido_id: int,
    estado_anterior: Optional[str],
    estado_nuevo: str,
    usuario_id: Optional[int] = None,
) -> HistorialPedido:
    """
    Apunta un nuevo evento en la trazabilidad del pedido. NO hace commit:
    se guarda junto con el cambio de estado que lo origina (misma transacción).
    """
    evento = HistorialPedido(
        pedido_id=pedido_id,
        estado_anterior=estado_anterior,
        estado_nuevo=estado_nuevo,
        usuario_id=usuario_id,
    )
    db.add(evento)
    asignar_codigo(db, evento, PREFIJO_HISTORIAL)  # codigo legible HP-001
    return evento


def listar_por_pedido(db: Session, pedido_id: int) -> List[HistorialPedido]:
    """Devuelve TODOS los eventos de un pedido en orden cronológico (CUS-35)."""
    return (
        db.query(HistorialPedido)
        .filter(HistorialPedido.pedido_id == pedido_id)
        .order_by(HistorialPedido.fecha_utc.asc(), HistorialPedido.id.asc())
        .all()
    )
