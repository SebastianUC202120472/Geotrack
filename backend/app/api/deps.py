# app/api/deps.py
# ============================================================================
# CAPA: API / DEPENDENCIAS — Seguridad transversal (JWT por rol)
# ----------------------------------------------------------------------------
# ¿QUÉ HACE?  Provee "porteros" reutilizables que protegen los endpoints:
#               - get_current_user      -> exige un JWT válido (cualquier usuario).
#               - get_current_conductor -> exige rol 'conductor' (App Móvil).
#               - get_current_admin     -> exige rol 'admin' (Panel Web).
# ¿CÓMO?      Lee el token del header Authorization, lo decodifica y busca al
#             usuario. Si algo falla, corta con 401/403.
# ¿CON QUÉ SE CONECTA?
#   - core/security.py -> para decodificar el token.
#   - models/usuario.py + db -> para recuperar al usuario.
#   - Lo USAN (con Depends): casi todos los endpoints de api/*.py.
# ============================================================================
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
