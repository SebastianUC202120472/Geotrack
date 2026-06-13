# app/services/vehiculo_service.py
# ============================================================================
# CAPA: SERVICIO (lógica de negocio) — Vehículos
# ----------------------------------------------------------------------------
# ¿QUÉ HACE?  Listar y registrar vehículos (evitando placas duplicadas).
# ¿CON QUÉ SE CONECTA?  repositories/vehiculo_repository.py ; lo usa api/vehiculos.py.
# ============================================================================
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories import vehiculo_repository
from app.schemas.vehiculo import VehiculoCreate


def listar_vehiculos(db: Session):
    """Devuelve los vehículos activos."""
    return vehiculo_repository.listar(db)


def crear_vehiculo(db: Session, datos: VehiculoCreate):
    """Registra un vehículo; rechaza si la placa ya existe."""
    if vehiculo_repository.obtener_por_placa(db, datos.placa):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un vehículo con esa placa",
        )
    vehiculo = vehiculo_repository.crear(
        db,
        placa=datos.placa,
        marca=datos.marca,
        capacidad_volumetrica=datos.capacidad_volumetrica,
        estado=datos.estado,
        conductor_id=datos.conductor_id,
    )
    db.commit()
    db.refresh(vehiculo)
    return vehiculo
