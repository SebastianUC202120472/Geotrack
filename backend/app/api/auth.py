from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_current_admin
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioResponse, Token, SolicitudRestablecimientoRequest
from app.services import usuario_service

router = APIRouter()


@router.post("/registro", response_model=UsuarioResponse)
def registrar_usuario(
    usuario: UsuarioCreate,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(get_current_admin),
):
    """Registra un usuario nuevo. Solo un admin autenticado puede hacerlo."""
    return usuario_service.registrar_usuario(db, usuario)


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Autentica con correo y contrasena, devuelve el token JWT."""
    access_token = usuario_service.autenticar_y_generar_token(
        db, correo=form_data.username, contrasena=form_data.password
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/solicitar-restablecimiento")
def solicitar_restablecimiento(datos: SolicitudRestablecimientoRequest, db: Session = Depends(get_db)):
    """Solicita restablecer contrasena (publico). Recibe correo del conductor."""
    return usuario_service.solicitar_restablecimiento(db, datos.correo)
