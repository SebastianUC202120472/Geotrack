# app/repositories/liquidacion_repository.py
# Única capa que escribe/lee la tabla 'liquidaciones' (CUS-36).
from typing import Optional
from sqlalchemy.orm import Session

from app.models.liquidacion import Liquidacion


def crear(db: Session, cliente_id: Optional[int], periodo_inicio, periodo_fin, url_documento: str) -> Liquidacion:
    """Registra una liquidación generada. Recibe: id del cliente (o None), rango de
    fechas y la ruta del .xlsx ya guardado. Devuelve el registro creado."""
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
    """Busca una liquidación por su id (para servir su archivo en la descarga)."""
    return db.query(Liquidacion).filter(Liquidacion.id == liquidacion_id).first()
