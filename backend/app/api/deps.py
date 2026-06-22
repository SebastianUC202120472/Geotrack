# app/api/deps.py
# Provee "porteros" reutilizables que protegen los endpoints.
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError

from app.db.database import get_db
from app.core.security import decode_access_token
from app.models.usuario import Usuario

# Apunta al endpoint de login ya existente (CUS-02). Swagger usará esto
# para el botón "Authorize".
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    """Decodifica el JWT, recupera el usuario y verifica que esté activo."""
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
    """Restringe el acceso a usuarios con rol 'conductor' (App Móvil)."""
    if usuario.rol != "conductor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta operación es exclusiva para conductores",
        )
    return usuario


def get_current_admin(usuario: Usuario = Depends(get_current_user)) -> Usuario:
    """Restringe el acceso a usuarios con rol 'admin' (Panel Web)."""
    if usuario.rol != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta operación es exclusiva para administradores",
        )
    return usuario


def get_current_almacen(usuario: Usuario = Depends(get_current_user)) -> Usuario:
    """Restringe el módulo de almacén (CUS-14) a usuarios con rol 'almacen' o 'admin'."""
    if usuario.rol not in ("almacen", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operación exclusiva del módulo de almacén",
        )
    return usuario
