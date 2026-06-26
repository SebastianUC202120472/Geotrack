# app/schemas/usuario.py
# Define los "moldes" de los datos que ENTRAN y SALEN por la API.
from enum import Enum
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator

from app.schemas.conductor import validar_fuerza_contrasena


class RolUsuario(str, Enum):
    """Roles válidos del sistema. Pydantic RECHAZA (422) cualquier otro valor,
    evitando que se cuelen roles inventados (seguridad / mínimo privilegio).
    ADMIN opera el panel; ALMACÉN es personal de almacén; CONDUCTOR usa la app."""
    ADMIN = "admin"
    ALMACEN = "almacen"
    CONDUCTOR = "conductor"


class UsuarioCreate(BaseModel):
    """Molde de ENTRADA: lo que el cliente envía para crear un usuario."""
    correo: EmailStr        # EmailStr valida que tenga formato de correo válido
    contrasena: str
    rol: RolUsuario         # admin / almacen / conductor (ver enum RolUsuario)


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


class SolicitudRestablecimientoRequest(BaseModel):
    """ENTRADA (extra CUS-04): el conductor pide restablecer su clave desde el Login."""
    correo: EmailStr


# --- CUS-03: gestión de usuarios del personal (admin/almacén) ---
class PersonalCreate(BaseModel):
    """ENTRADA (CUS-03): el admin crea una cuenta de personal con su rol."""
    correo: EmailStr
    contrasena: str
    rol: RolUsuario

    @field_validator("contrasena")
    @classmethod
    def _v_contrasena(cls, v: str) -> str:
        return validar_fuerza_contrasena(v)

    @field_validator("rol")
    @classmethod
    def _v_rol(cls, v: RolUsuario) -> RolUsuario:
        # Los conductores se gestionan en su propia sección (con perfil/vehículo).
        if v == RolUsuario.CONDUCTOR:
            raise ValueError("Los conductores se crean en la sección Conductores")
        return v


class PersonalUpdate(BaseModel):
    """ENTRADA (CUS-03): cambiar el rol y/o el estado (activo) de un usuario."""
    rol: Optional[RolUsuario] = None
    estado: Optional[bool] = None

    @field_validator("rol")
    @classmethod
    def _v_rol(cls, v: Optional[RolUsuario]) -> Optional[RolUsuario]:
        if v == RolUsuario.CONDUCTOR:
            raise ValueError("No se puede convertir una cuenta de panel en conductor aquí")
        return v


class PersonalResetContrasena(BaseModel):
    """ENTRADA (CUS-03): el admin fija una nueva contraseña para un usuario del panel."""
    contrasena: str

    @field_validator("contrasena")
    @classmethod
    def _v_contrasena(cls, v: str) -> str:
        return validar_fuerza_contrasena(v)
