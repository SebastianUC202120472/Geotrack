# app/services/vehiculo_service.py
# Listar y registrar vehículos (evitando placas duplicadas).
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories import vehiculo_repository, conductor_repository
from app.schemas.vehiculo import VehiculoCreate


def listar_vehiculos(db: Session):
    """Devuelve los vehículos activos. El estado se recalcula: si el conductor del
    vehículo tiene una ruta activa, el vehículo aparece EN_RUTA (no DISPONIBLE)."""
    vehiculos = vehiculo_repository.listar(db)
    salida = []
    for v in vehiculos:
        estado = v.estado
        if v.conductor_id and conductor_repository.tiene_ruta_activa(db, v.conductor_id):
            estado = "EN_RUTA"
        salida.append({
            "id": v.id,
            "codigo": v.codigo,
            "placa": v.placa,
            "marca": v.marca,
            "capacidad_volumetrica": v.capacidad_volumetrica,
            "estado": estado,
            "conductor_id": v.conductor_id,
        })
    return salida


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
