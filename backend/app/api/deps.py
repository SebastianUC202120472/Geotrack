from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError

from app.db.database import get_db
from app.core.security import decode_access_token
from app.models.usuario import Usuario

# Esquema OAuth2; apunta al login para el botón "Authorize" de Swagger.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    """Decodifica el JWT y devuelve el usuario activo. Recibe token y sesion de BD."""
    credenciales_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        correo: str | None = payload.get("sub")
        if correo is None:
            raise credenciales_invalidas
    except JWTError:
        raise credenciales_invalidas

    usuario = db.query(Usuario).filter(Usuario.correo == correo).first()
    if usuario is None or not usuario.estado:
        raise credenciales_invalidas

    return usuario


def get_current_conductor(usuario: Usuario = Depends(get_current_user)) -> Usuario:
    """Valida que el usuario tenga rol conductor. Recibe usuario autenticado."""
    if usuario.rol != "conductor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta operación es exclusiva para conductores",
        )
    return usuario


def get_current_admin(usuario: Usuario = Depends(get_current_user)) -> Usuario:
    """Valida que el usuario tenga rol admin. Recibe usuario autenticado."""
    if usuario.rol != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta operación es exclusiva para administradores",
        )
    return usuario


def get_current_almacen(usuario: Usuario = Depends(get_current_user)) -> Usuario:
    """Valida que el usuario tenga rol almacen o admin. Recibe usuario autenticado."""
    if usuario.rol not in ("almacen", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operación exclusiva del módulo de almacén",
        )
    return usuario
