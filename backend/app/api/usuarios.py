from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_current_admin, get_current_almacen
from app.models.usuario import Usuario
from app.services import usuario_service
from app.schemas.usuario import UsuarioResponse, PersonalCreate, PersonalUpdate, PersonalResetContrasena

router = APIRouter()


@router.get("/yo", response_model=UsuarioResponse)
def mi_perfil(usuario: Usuario = Depends(get_current_almacen)):
    """Devuelve los datos del usuario de panel autenticado (admin o almacén)."""
    return usuario


@router.get("/", response_model=List[UsuarioResponse], dependencies=[Depends(get_current_admin)])
def listar_personal(db: Session = Depends(get_db)):
    """Lista las cuentas del panel (admin/almacén)."""
    return usuario_service.listar_personal(db)


@router.post("/", response_model=UsuarioResponse, dependencies=[Depends(get_current_admin)])
def crear_personal(datos: PersonalCreate, db: Session = Depends(get_db)):
    """Crea una cuenta de personal con su rol (admin/almacén)."""
    return usuario_service.crear_personal(db, datos)


@router.patch("/{usuario_id}", response_model=UsuarioResponse, dependencies=[Depends(get_current_admin)])
def actualizar_personal(
    usuario_id: int,
    datos: PersonalUpdate,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(get_current_admin),
):
    """Actualiza rol y/o estado de un usuario del panel. Recibe usuario_id y datos."""
    return usuario_service.actualizar_personal(db, usuario_id, datos, admin.id)


@router.post("/{usuario_id}/restablecer-contrasena", dependencies=[Depends(get_current_admin)])
def restablecer_contrasena(usuario_id: int, datos: PersonalResetContrasena, db: Session = Depends(get_db)):
    """Restablece la contraseña de un usuario del panel. Recibe usuario_id y nueva contraseña."""
    return usuario_service.restablecer_contrasena_personal(db, usuario_id, datos)
