# app/api/conductores.py
# GET /api/conductores -> lista de conductores con su ficha y el vehículo asignado.
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_current_admin
from app.services import conductor_service
from app.schemas.conductor import ConductorCreate, ConductorResponse

router = APIRouter()


@router.get("/", response_model=List[ConductorResponse], dependencies=[Depends(get_current_admin)])
def listar_conductores(db: Session = Depends(get_db)):
    """Lista los conductores con sus datos y el vehículo que tienen asignado."""
    return conductor_service.listar(db)


@router.post("/", response_model=ConductorResponse, dependencies=[Depends(get_current_admin)])
def crear_conductor(datos: ConductorCreate, db: Session = Depends(get_db)):
    """Registra un conductor: crea su cuenta (rol conductor) y su ficha de datos."""
    return conductor_service.crear(db, datos)
