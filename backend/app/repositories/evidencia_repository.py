from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.models.evidencia import EvidenciaEntrega


def obtener_por_pedido(db: Session, pedido_id: int) -> Optional[EvidenciaEntrega]:
    """Devuelve la evidencia (POD) de un pedido, si existe."""
    return db.query(EvidenciaEntrega).filter(EvidenciaEntrega.pedido_id == pedido_id).first()


def registrar_foto(db: Session, pedido_id: int, url_foto: str, geo: Optional[str] = None) -> EvidenciaEntrega:
    """Crea o actualiza la evidencia fotográfica de un pedido. Recibe pedido_id, url_foto y geo opcional."""
    evidencia = obtener_por_pedido(db, pedido_id)
    if evidencia is None:
        evidencia = EvidenciaEntrega(pedido_id=pedido_id)
        db.add(evidencia)
    evidencia.url_foto = url_foto
    if geo is not None:
        evidencia.latitud_longitud_captura = geo
    evidencia.fecha_hora = datetime.utcnow()
    db.commit()
    db.refresh(evidencia)
    return evidencia
