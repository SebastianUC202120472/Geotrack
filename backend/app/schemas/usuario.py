from enum import Enum
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator

from app.schemas.conductor import validar_fuerza_contrasena


class RolUsuario(str, Enum):
    """Roles válidos del sistema; Pydantic rechaza cualquier otro valor."""
    ADMIN = "admin"
    ALMACEN = "almacen"
    CONDUCTOR = "conductor"


class UsuarioCreate(BaseModel):
    """Datos de entrada para crear un usuario."""
    correo: EmailStr
    contrasena: str
    rol: RolUsuario


class UsuarioResponse(BaseModel):
    """Datos de salida del usuario, sin contraseña."""
    id: int
    codigo: Optional[str] = None
    correo: EmailStr
    rol: str
    estado: bool
    nombre: Optional[str] = None
    dni: Optional[str] = None
    telefono: Optional[str] = None
    cargo: Optional[str] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Respuesta del login: token JWT y tipo."""
    access_token: str
    token_type: str


class SolicitudRestablecimientoRequest(BaseModel):
    """Datos de entrada para solicitar restablecimiento de contraseña."""
    correo: EmailStr


class PersonalCreate(BaseModel):
    """Datos de entrada para crear personal de panel (admin o almacen)."""
    correo: EmailStr
    contrasena: str
    rol: RolUsuario
    nombre: Optional[str] = None
    dni: Optional[str] = None
    telefono: Optional[str] = None
    cargo: Optional[str] = None

    @field_validator("contrasena")
    @classmethod
    def _v_contrasena(cls, v: str) -> str:
        return validar_fuerza_contrasena(v)

    @field_validator("rol")
    @classmethod
    def _v_rol(cls, v: RolUsuario) -> RolUsuario:
        if v == RolUsuario.CONDUCTOR:
            raise ValueError("Los conductores se crean en la sección Conductores")
        return v


class PersonalUpdate(BaseModel):
    """Datos de entrada para actualizar rol, estado o datos personales del personal."""
    rol: Optional[RolUsuario] = None
    estado: Optional[bool] = None
    nombre: Optional[str] = None
    dni: Optional[str] = None
    telefono: Optional[str] = None
    cargo: Optional[str] = None

    @field_validator("rol")
    @classmethod
    def _v_rol(cls, v: Optional[RolUsuario]) -> Optional[RolUsuario]:
        if v == RolUsuario.CONDUCTOR:
            raise ValueError("No se puede convertir una cuenta de panel en conductor aquí")
        return v


class PersonalResetContrasena(BaseModel):
    """Datos de entrada para resetear la contraseña de un usuario del panel."""
    contrasena: str

    @field_validator("contrasena")
    @classmethod
    def _v_contrasena(cls, v: str) -> str:
        return validar_fuerza_contrasena(v)
