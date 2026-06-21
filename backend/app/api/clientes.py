# app/api/clientes.py
# El "apartado de clientes" del panel web del admin (Fase 4 / tesis).
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_current_admin
from app.services import cliente_service
from app.schemas.cliente import ClienteCreate, ClienteResponse, ClienteUpdate

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
    """CUS-07: edita los datos de una empresa cliente."""
    return cliente_service.actualizar_cliente(db, cliente_id, datos)


@router.delete("/{cliente_id}", dependencies=[Depends(get_current_admin)])
def eliminar_cliente(cliente_id: int, db: Session = Depends(get_db)):
    """CUS-07: da de baja una empresa cliente (borrado lógico)."""
    return cliente_service.eliminar_cliente(db, cliente_id)
