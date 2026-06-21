# app/repositories/vehiculo_repository.py
# Consultas/escritura de la tabla 'vehiculos'.
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.vehiculo import Vehiculo
from app.core.codigos import asignar_codigo, PREFIJO_VEHICULO


def listar(db: Session) -> List[Vehiculo]:
    """Lista los vehículos activos (no borrados lógicamente)."""
    return (
        db.query(Vehiculo)
        .filter(Vehiculo.eliminado_en == None)  # noqa: E711
        .order_by(Vehiculo.placa.asc())
        .all()
    )


def obtener_por_placa(db: Session, placa: str) -> Optional[Vehiculo]:
    """Busca un vehículo por su placa (única)."""
    return db.query(Vehiculo).filter(Vehiculo.placa == placa).first()


def obtener_por_id(db: Session, vehiculo_id: int) -> Optional[Vehiculo]:
    """Busca un vehículo activo por su id (no borrado lógicamente)."""
    return (
        db.query(Vehiculo)
        .filter(Vehiculo.id == vehiculo_id, Vehiculo.eliminado_en == None)  # noqa: E711
        .first()
    )


def crear(db: Session, placa: str, marca=None, capacidad_volumetrica=None,
          capacidad_cajas=None, estado="DISPONIBLE", conductor_id=None) -> Vehiculo:
    """Crea un vehículo con su código legible VE-001 (hace flush para obtener id)."""
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
    """Cambia el conductor asignado a un vehículo (CUS-09). Mantiene la relación 1-a-1:
    si el conductor ya tenía OTRO vehículo, ese se libera. Recibe: el vehículo y el
    nuevo conductor_id (None = lo deja como vehículo de la empresa)."""
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
    """Baja lógica de un vehículo (CUS-08): marca eliminado_en y libera su conductor.
    Recibe: el vehículo. No borra físicamente (conserva trazabilidad)."""
    vehiculo.eliminado_en = datetime.utcnow()
    vehiculo.conductor_id = None
    db.commit()
