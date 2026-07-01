from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.models.ubicacion import UbicacionConductor


def obtener(db: Session, conductor_id: int) -> Optional[UbicacionConductor]:
    """Última posición conocida del conductor (o None si nunca envió)."""
    return db.query(UbicacionConductor).filter(UbicacionConductor.conductor_id == conductor_id).first()


def upsert(db: Session, conductor_id: int, latitud: float, longitud: float) -> UbicacionConductor:
    """Inserta o actualiza la última posición del conductor. Recibe conductor_id, latitud y longitud."""
    ubicacion = obtener(db, conductor_id)
    if ubicacion:
        ubicacion.latitud = latitud
        ubicacion.longitud = longitud
        ubicacion.actualizado_en = datetime.utcnow()
    else:
        ubicacion = UbicacionConductor(
            conductor_id=conductor_id, latitud=latitud, longitud=longitud, actualizado_en=datetime.utcnow()
        )
        db.add(ubicacion)
    db.commit()
    db.refresh(ubicacion)
    return ubicacion
