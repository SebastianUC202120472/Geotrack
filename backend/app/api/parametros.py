# Catálogos administrables del sistema (motivos de rechazo y combustible). Solo admin.
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_current_admin
from app.services import parametro_service
from app.schemas.parametro import MotivoCreate, MotivoResponse, CombustibleConfig, ContactoConfig, FranjasConfig

router = APIRouter()


@router.get("/motivos", response_model=List[MotivoResponse], dependencies=[Depends(get_current_admin)])
def listar_motivos(db: Session = Depends(get_db)):
    """Lista los motivos de rechazo del catálogo."""
    return parametro_service.listar_motivos(db)


@router.post("/motivos", response_model=MotivoResponse, dependencies=[Depends(get_current_admin)])
def crear_motivo(datos: MotivoCreate, db: Session = Depends(get_db)):
    """Agrega un motivo de rechazo. Recibe el texto del motivo."""
    return parametro_service.crear_motivo(db, datos.texto)


@router.delete("/motivos/{motivo_id}", dependencies=[Depends(get_current_admin)])
def eliminar_motivo(motivo_id: int, db: Session = Depends(get_db)):
    """Elimina un motivo de rechazo. Recibe motivo_id."""
    return parametro_service.eliminar_motivo(db, motivo_id)


@router.get("/combustible", response_model=CombustibleConfig, dependencies=[Depends(get_current_admin)])
def obtener_combustible(db: Session = Depends(get_db)):
    """Lee los parámetros de combustible (consumo y precio)."""
    return parametro_service.obtener_combustible(db)


@router.put("/combustible", response_model=CombustibleConfig, dependencies=[Depends(get_current_admin)])
def actualizar_combustible(datos: CombustibleConfig, db: Session = Depends(get_db)):
    """Actualiza los parámetros de combustible. Recibe consumo y precio por litro."""
    return parametro_service.actualizar_combustible(db, datos.consumo_l_100km, datos.precio_soles_litro)


@router.get("/contacto", response_model=ContactoConfig, dependencies=[Depends(get_current_admin)])
def obtener_contacto(db: Session = Depends(get_db)):
    """Lee el telefono de coordinacion que usa la app del conductor."""
    return parametro_service.obtener_contacto(db)


@router.put("/contacto", response_model=ContactoConfig, dependencies=[Depends(get_current_admin)])
def actualizar_contacto(datos: ContactoConfig, db: Session = Depends(get_db)):
    """Actualiza el telefono de coordinacion. Recibe el telefono (vacio lo borra)."""
    return parametro_service.actualizar_contacto(db, datos.telefono_coordinacion)


@router.get("/franjas", response_model=FranjasConfig, dependencies=[Depends(get_current_admin)])
def obtener_franjas(db: Session = Depends(get_db)):
    """Lee las franjas de reprogramacion que ofrece el portal."""
    return {"franjas": parametro_service.obtener_franjas(db)}


@router.put("/franjas", response_model=FranjasConfig, dependencies=[Depends(get_current_admin)])
def actualizar_franjas(datos: FranjasConfig, db: Session = Depends(get_db)):
    """Actualiza las franjas de reprogramacion del portal. Recibe la lista de franjas."""
    return {"franjas": parametro_service.actualizar_franjas(db, datos.franjas)}
