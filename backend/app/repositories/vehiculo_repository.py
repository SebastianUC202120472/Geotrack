from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.vehiculo import Vehiculo
from app.core.codigos import asignar_codigo, PREFIJO_VEHICULO


def listar(db: Session) -> List[Vehiculo]:
    """Lista vehiculos activos (sin baja logica)."""
    return (
        db.query(Vehiculo)
        .filter(Vehiculo.eliminado_en == None)  # noqa: E711
        .order_by(Vehiculo.placa.asc())
        .all()
    )


def obtener_por_placa(db: Session, placa: str) -> Optional[Vehiculo]:
    """Busca un vehiculo por placa. Recibe: placa."""
    return db.query(Vehiculo).filter(Vehiculo.placa == placa).first()


def obtener_por_id(db: Session, vehiculo_id: int) -> Optional[Vehiculo]:
    """Busca un vehiculo activo por id. Recibe: vehiculo_id."""
    return (
        db.query(Vehiculo)
        .filter(Vehiculo.id == vehiculo_id, Vehiculo.eliminado_en == None)  # noqa: E711
        .first()
    )


def crear(db: Session, placa: str, marca=None, capacidad_volumetrica=None,
          capacidad_cajas=None, estado="DISPONIBLE", conductor_id=None) -> Vehiculo:
    """Crea un vehiculo y le asigna codigo VE-001. Recibe: placa y datos opcionales."""
    vehiculo = Vehiculo(
        placa=placa,
        marca=marca,
        capacidad_volumetrica=capacidad_volumetrica,
        capacidad_cajas=capacidad_cajas,
        estado=estado or "DISPONIBLE",
        conductor_id=conductor_id,
    )
    db.add(vehiculo)
    asignar_codigo(db, vehiculo, PREFIJO_VEHICULO)
    return vehiculo


def reasignar_conductor(db: Session, vehiculo: Vehiculo, conductor_id: Optional[int]) -> Vehiculo:
    """Asigna conductor a un vehiculo liberando el previo si aplica. Recibe: vehiculo y conductor_id (None = sin conductor)."""
    if conductor_id is not None:
        previo = (
            db.query(Vehiculo)
            .filter(Vehiculo.conductor_id == conductor_id, Vehiculo.id != vehiculo.id)
            .first()
        )
        if previo:
            previo.conductor_id = None
    vehiculo.conductor_id = conductor_id
    db.commit()
    db.refresh(vehiculo)
    return vehiculo


def eliminar(db: Session, vehiculo: Vehiculo) -> None:
    """Baja logica del vehiculo: marca eliminado_en y libera conductor. Recibe: vehiculo."""
    vehiculo.eliminado_en = datetime.utcnow()
    vehiculo.conductor_id = None
    db.commit()
