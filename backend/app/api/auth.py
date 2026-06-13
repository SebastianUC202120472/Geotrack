# app/api/auth.py
# Expone las URLs de autenticación que consumen la Web y la App.
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_current_admin
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioResponse, Token
from app.services import usuario_service

router = APIRouter()


@router.post("/registro", response_model=UsuarioResponse)
def registrar_usuario(
    usuario: UsuarioCreate,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(get_current_admin),
):
    """
    Registra un usuario nuevo (CUS-01) — SOLO un admin puede hacerlo.
    SEGURIDAD (OWASP A01): antes estaba abierto y aceptaba el 'rol' del cliente,
    así que cualquiera podía crearse como admin (escalada de privilegios). Ahora
    solo un admin autenticado da de alta usuarios.
    FRONTEND: el alta de usuarios va en el panel del admin (con su token). El
    primer admin se crea solo al arrancar (ver crear_admin_inicial / .env).
    """
    return usuario_service.registrar_usuario(db, usuario)


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Inicia sesión (CUS-02) y devuelve el token JWT.
    Usa OAuth2PasswordRequestForm: el cliente envía 'username' (=correo) y
    'password'. Es lo que rellena el botón "Authorize" de Swagger.
    """
    access_token = usuario_service.autenticar_y_generar_token(
        db, correo=form_data.username, contrasena=form_data.password
    )
    return {"access_token": access_token, "token_type": "bearer"}
