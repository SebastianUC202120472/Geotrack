from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_current_admin
from app.services import cliente_service
from app.schemas.cliente import AccesoPortalIn, ClienteCreate, ClienteResponse, ClienteUpdate

router = APIRouter()


@router.get("/", response_model=List[ClienteResponse], dependencies=[Depends(get_current_admin)])
def listar_clientes(db: Session = Depends(get_db)):
    """Lista las empresas cliente registradas."""
    return cliente_service.listar_clientes(db)


@router.post("/", response_model=ClienteResponse, dependencies=[Depends(get_current_admin)])
def crear_cliente(datos: ClienteCreate, db: Session = Depends(get_db)):
    """Registra una empresa cliente (también se crean solas al cargar el Excel)."""
    return cliente_service.crear_cliente(db, datos)


@router.patch("/{cliente_id}", response_model=ClienteResponse, dependencies=[Depends(get_current_admin)])
def actualizar_cliente(cliente_id: int, datos: ClienteUpdate, db: Session = Depends(get_db)):
    """Edita los datos de una empresa cliente. Recibe cliente_id y datos parciales."""
    return cliente_service.actualizar_cliente(db, cliente_id, datos)


@router.delete("/{cliente_id}", dependencies=[Depends(get_current_admin)])
def eliminar_cliente(cliente_id: int, db: Session = Depends(get_db)):
    """Da de baja una empresa cliente (borrado logico). Recibe cliente_id."""
    return cliente_service.eliminar_cliente(db, cliente_id)


@router.post("/{cliente_id}/acceso-portal", dependencies=[Depends(get_current_admin)])
def generar_acceso(cliente_id: int, datos: AccesoPortalIn, db: Session = Depends(get_db)):
    """Genera/reinicia el acceso al portal de un cliente. Recibe id y {correoPortal}."""
    return cliente_service.generar_acceso_portal(db, cliente_id, datos.correoPortal)


@router.delete("/{cliente_id}/acceso-portal", dependencies=[Depends(get_current_admin)])
def revocar_acceso(cliente_id: int, db: Session = Depends(get_db)):
    """Revoca el acceso al portal de un cliente. Recibe el id."""
    return cliente_service.revocar_acceso_portal(db, cliente_id)
