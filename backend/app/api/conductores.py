# app/api/conductores.py
# GET /api/conductores -> lista de conductores con su ficha y el vehículo asignado.
from typing import List
from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_current_admin
from app.services import conductor_service
from app.schemas.conductor import ConductorCreate, ConductorResponse, ConductorUpdate, ConductorResetContrasena

router = APIRouter()


@router.get("/", response_model=List[ConductorResponse], dependencies=[Depends(get_current_admin)])
def listar_conductores(db: Session = Depends(get_db)):
    """Lista los conductores con sus datos y el vehículo que tienen asignado."""
    return conductor_service.listar(db)


@router.post("/", response_model=ConductorResponse, dependencies=[Depends(get_current_admin)])
def crear_conductor(datos: ConductorCreate, db: Session = Depends(get_db)):
    """Registra un conductor: crea su cuenta (rol conductor) y su ficha de datos."""
    return conductor_service.crear(db, datos)


@router.patch("/{usuario_id}", response_model=ConductorResponse, dependencies=[Depends(get_current_admin)])
def actualizar_conductor(usuario_id: int, datos: ConductorUpdate, db: Session = Depends(get_db)):
    """Edita la ficha (nombre/teléfono/DNI) de un conductor."""
    return conductor_service.actualizar(db, usuario_id, datos)


@router.delete("/{usuario_id}", dependencies=[Depends(get_current_admin)])
def eliminar_conductor(usuario_id: int, db: Session = Depends(get_db)):
    """Elimina (desactiva) un conductor; preserva su historial y libera su vehículo."""
    return conductor_service.eliminar(db, usuario_id)


@router.post("/{usuario_id}/restablecer-contrasena", dependencies=[Depends(get_current_admin)])
def restablecer_contrasena(usuario_id: int, datos: ConductorResetContrasena, db: Session = Depends(get_db)):
    """CUS-04: el admin fija una nueva contraseña para un conductor que la olvidó."""
    return conductor_service.restablecer_contrasena(db, usuario_id, datos)


@router.post("/{usuario_id}/foto", response_model=ConductorResponse, dependencies=[Depends(get_current_admin)])
async def subir_foto_conductor(
    usuario_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Sube/reemplaza la foto del conductor (la verá en su app móvil)."""
    contenido = await file.read()
    return conductor_service.guardar_foto(db, usuario_id, contenido, file.filename)
