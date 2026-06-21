# app/api/parametros.py
# Catálogos administrables del sistema (CUS-06). Por ahora, motivos de rechazo. Solo-admin.
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_current_admin
from app.services import parametro_service
from app.schemas.parametro import MotivoCreate, MotivoResponse, CombustibleConfig

router = APIRouter()


@router.get("/motivos", response_model=List[MotivoResponse], dependencies=[Depends(get_current_admin)])
def listar_motivos(db: Session = Depends(get_db)):
    """CUS-06: lista los motivos de rechazo del catálogo."""
    return parametro_service.listar_motivos(db)


@router.post("/motivos", response_model=MotivoResponse, dependencies=[Depends(get_current_admin)])
def crear_motivo(datos: MotivoCreate, db: Session = Depends(get_db)):
    """CUS-06: agrega un motivo de rechazo."""
    return parametro_service.crear_motivo(db, datos.texto)


@router.delete("/motivos/{motivo_id}", dependencies=[Depends(get_current_admin)])
def eliminar_motivo(motivo_id: int, db: Session = Depends(get_db)):
    """CUS-06: elimina un motivo de rechazo del catálogo."""
    return parametro_service.eliminar_motivo(db, motivo_id)


@router.get("/combustible", response_model=CombustibleConfig, dependencies=[Depends(get_current_admin)])
def obtener_combustible(db: Session = Depends(get_db)):
    """CUS-34: lee los parámetros de combustible (consumo y precio)."""
    return parametro_service.obtener_combustible(db)


@router.put("/combustible", response_model=CombustibleConfig, dependencies=[Depends(get_current_admin)])
def actualizar_combustible(datos: CombustibleConfig, db: Session = Depends(get_db)):
    """CUS-34: actualiza los parámetros de combustible."""
    return parametro_service.actualizar_combustible(db, datos.consumo_l_100km, datos.precio_soles_litro)
