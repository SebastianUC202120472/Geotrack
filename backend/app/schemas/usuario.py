# app/schemas/usuario.py
# Define los "moldes" de los datos que ENTRAN y SALEN por la API.
from enum import Enum
from typing import Optional
from pydantic import BaseModel, EmailStr


class RolUsuario(str, Enum):
    """Roles válidos del sistema. Pydantic RECHAZA (422) cualquier otro valor,
    evitando que se cuelen roles inventados (seguridad / mínimo privilegio)."""
    ADMIN = "admin"
    CONDUCTOR = "conductor"


class UsuarioCreate(BaseModel):
    """Molde de ENTRADA: lo que el cliente envía para crear un usuario."""
    correo: EmailStr        # EmailStr valida que tenga formato de correo válido
    contrasena: str
    rol: RolUsuario         # solo se acepta 'admin' o 'conductor'


class UsuarioResponse(BaseModel):
    """Molde de SALIDA: lo que devolvemos al cliente (SIN la contraseña)."""
    id: int
    codigo: Optional[str] = None  # AD-001 / CO-001
    correo: EmailStr
    rol: str
    estado: bool

    class Config:
        from_attributes = True  # permite construir el schema desde un objeto SQLAlchemy


class Token(BaseModel):
    """Molde de SALIDA del login: el token JWT y su tipo."""
    access_token: str
    token_type: str
