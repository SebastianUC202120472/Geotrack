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


def obtener_por_conductor(db: Session, conductor_id) -> Optional[Vehiculo]:
    """Busca el vehiculo activo asignado a un conductor. Recibe: conductor_id (puede ser None)."""
    if not conductor_id:
        return None
    return (
        db.query(Vehiculo)
        .filter(Vehiculo.conductor_id == conductor_id, Vehiculo.eliminado_en == None)  # noqa: E711
        .first()
    )


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


def liberar_otros_de(db: Session, conductor_id: int, excepto_id: Optional[int] = None) -> None:
    """Quita al conductor de cualquier otro vehiculo (regla 1 a 1, RN-07). Recibe conductor_id y el vehiculo a conservar."""
    otros = db.query(Vehiculo).filter(Vehiculo.conductor_id == conductor_id)
    if excepto_id is not None:
        otros = otros.filter(Vehiculo.id != excepto_id)
    for previo in otros.all():
        previo.conductor_id = None


def reasignar_conductor(db: Session, vehiculo: Vehiculo, conductor_id: Optional[int]) -> Vehiculo:
    """Asigna conductor a un vehiculo liberando el previo si aplica. Recibe: vehiculo y conductor_id (None = sin conductor)."""
    if conductor_id is not None:
        liberar_otros_de(db, conductor_id, excepto_id=vehiculo.id)
    vehiculo.conductor_id = conductor_id
    db.commit()
    db.refresh(vehiculo)
    return vehiculo


def eliminar(db: Session, vehiculo: Vehiculo) -> None:
    """Baja logica del vehiculo: marca eliminado_en y libera conductor. Recibe: vehiculo."""
    vehiculo.eliminado_en = datetime.utcnow()
    vehiculo.conductor_id = None
    db.commit()
