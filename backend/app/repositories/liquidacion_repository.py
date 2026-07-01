from typing import Optional
from sqlalchemy.orm import Session

from app.models.liquidacion import Liquidacion


def crear(db: Session, cliente_id: Optional[int], periodo_inicio, periodo_fin, url_documento: str) -> Liquidacion:
    """Inserta una liquidacion en BD. Recibe cliente_id opcional, rango de fechas y url del documento."""
    liquidacion = Liquidacion(
        cliente_id=cliente_id,
        periodo_inicio=periodo_inicio,
        periodo_fin=periodo_fin,
        url_documento=url_documento,
    )
    db.add(liquidacion)
    db.commit()
    db.refresh(liquidacion)
    return liquidacion


def obtener_por_id(db: Session, liquidacion_id: int) -> Optional[Liquidacion]:
    """Busca una liquidacion por su id. Recibe liquidacion_id."""
    return db.query(Liquidacion).filter(Liquidacion.id == liquidacion_id).first()
