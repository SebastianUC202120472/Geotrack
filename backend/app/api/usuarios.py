# app/api/usuarios.py
# Gestión de las cuentas del PANEL (admin/almacén) — CUS-03. Los conductores
# se gestionan en su propia sección (con perfil y vehículo). Todo aquí es solo-admin.
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_current_admin
from app.models.usuario import Usuario
from app.services import usuario_service
from app.schemas.usuario import UsuarioResponse, PersonalCreate, PersonalUpdate, PersonalResetContrasena

router = APIRouter()


@router.get("/", response_model=List[UsuarioResponse], dependencies=[Depends(get_current_admin)])
def listar_personal(db: Session = Depends(get_db)):
    """CUS-03: lista las cuentas del panel (admin/almacén)."""
    return usuario_service.listar_personal(db)


@router.post("/", response_model=UsuarioResponse, dependencies=[Depends(get_current_admin)])
def crear_personal(datos: PersonalCreate, db: Session = Depends(get_db)):
    """CUS-03: crea una cuenta de personal con su rol (admin/almacén)."""
    return usuario_service.crear_personal(db, datos)


@router.patch("/{usuario_id}", response_model=UsuarioResponse, dependencies=[Depends(get_current_admin)])
def actualizar_personal(
    usuario_id: int,
    datos: PersonalUpdate,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(get_current_admin),
):
    """CUS-03: cambia el rol y/o el estado (activo) de un usuario del panel."""
    return usuario_service.actualizar_personal(db, usuario_id, datos, admin.id)


@router.post("/{usuario_id}/restablecer-contrasena", dependencies=[Depends(get_current_admin)])
def restablecer_contrasena(usuario_id: int, datos: PersonalResetContrasena, db: Session = Depends(get_db)):
    """CUS-03: el admin fija una nueva contraseña para un usuario del panel."""
    return usuario_service.restablecer_contrasena_personal(db, usuario_id, datos)
