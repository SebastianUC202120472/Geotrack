# app/api/vehiculos.py
# GET /api/vehiculos -> listar la flota POST /api/vehiculos -> registrar un vehículo SEGURIDAD.
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_current_admin
from app.services import vehiculo_service
from app.schemas.vehiculo import VehiculoCreate, VehiculoResponse, VehiculoUpdate

router = APIRouter()


@router.get("/", response_model=List[VehiculoResponse], dependencies=[Depends(get_current_admin)])
def listar_vehiculos(db: Session = Depends(get_db)):
    """Lista los vehículos de la flota."""
    return vehiculo_service.listar_vehiculos(db)


@router.post("/", response_model=VehiculoResponse, dependencies=[Depends(get_current_admin)])
def crear_vehiculo(datos: VehiculoCreate, db: Session = Depends(get_db)):
    """Registra un vehículo (de un conductor o de la empresa si conductor_id es null)."""
    return vehiculo_service.crear_vehiculo(db, datos)


@router.patch("/{vehiculo_id}", response_model=VehiculoResponse, dependencies=[Depends(get_current_admin)])
def actualizar_vehiculo(vehiculo_id: int, datos: VehiculoUpdate, db: Session = Depends(get_db)):
    """CUS-08/09: edita un vehículo (marca/capacidades) y/o reasigna su conductor."""
    return vehiculo_service.actualizar_vehiculo(db, vehiculo_id, datos)


@router.delete("/{vehiculo_id}", dependencies=[Depends(get_current_admin)])
def eliminar_vehiculo(vehiculo_id: int, db: Session = Depends(get_db)):
    """CUS-08: da de baja un vehículo (borrado lógico) y libera su conductor."""
    return vehiculo_service.eliminar_vehiculo(db, vehiculo_id)
