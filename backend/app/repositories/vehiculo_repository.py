# app/repositories/vehiculo_repository.py
# ============================================================================
# CAPA: REPOSITORIO (acceso a datos) — Vehículos
# ----------------------------------------------------------------------------
# ¿QUÉ HACE?  Consultas/escritura de la tabla 'vehiculos'.
# ¿CON QUÉ SE CONECTA?  models/vehiculo.py ; lo usa services/vehiculo_service.py.
# ============================================================================
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


def crear(db: Session, placa: str, marca=None, capacidad_volumetrica=None,
          estado="DISPONIBLE", conductor_id=None) -> Vehiculo:
    """Crea un vehículo con su código legible VE-001 (hace flush para obtener id)."""
    vehiculo = Vehiculo(
        placa=placa,
        marca=marca,
        capacidad_volumetrica=capacidad_volumetrica,
        estado=estado or "DISPONIBLE",
        conductor_id=conductor_id,
    )
    db.add(vehiculo)
    asignar_codigo(db, vehiculo, PREFIJO_VEHICULO)
    return vehiculo
