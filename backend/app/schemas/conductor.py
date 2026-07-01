import re
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator

_RE_TELEFONO = re.compile(r"^9\d{8}$")
_RE_DNI = re.compile(r"^\d{8}$")


def validar_fuerza_contrasena(v: str) -> str:
    """Valida fuerza de contraseña (min 8, mayus, minus, numero, especial). Recibe: la clave."""
    if len(v) < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres")
    if not re.search(r"[A-Z]", v):
        raise ValueError("La contraseña debe incluir al menos una mayúscula")
    if not re.search(r"[a-z]", v):
        raise ValueError("La contraseña debe incluir al menos una minúscula")
    if not re.search(r"\d", v):
        raise ValueError("La contraseña debe incluir al menos un número")
    if not re.search(r"[^A-Za-z0-9]", v):
        raise ValueError("La contraseña debe incluir al menos un carácter especial")
    return v


class ConductorCreate(BaseModel):
    """Datos para dar de alta un conductor. Recibe correo, contrasena, nombre y datos opcionales."""
    correo: EmailStr
    contrasena: str
    nombre: str
    telefono: Optional[str] = None
    dni: Optional[str] = None

    @field_validator("nombre")
    @classmethod
    def _v_nombre(cls, v: str) -> str:
        v = (v or "").strip()
        if len(v) < 3:
            raise ValueError("El nombre debe tener al menos 3 caracteres")
        return v

    @field_validator("contrasena")
    @classmethod
    def _v_contrasena(cls, v: str) -> str:
        return validar_fuerza_contrasena(v)

    @field_validator("telefono")
    @classmethod
    def _v_telefono(cls, v: Optional[str]) -> Optional[str]:
        if v in (None, ""):
            return None
        v = v.strip().replace(" ", "")
        if not _RE_TELEFONO.match(v):
            raise ValueError("El teléfono debe tener 9 dígitos y empezar en 9")
        return v

    @field_validator("dni")
    @classmethod
    def _v_dni(cls, v: Optional[str]) -> Optional[str]:
        if v in (None, ""):
            return None
        v = v.strip()
        if not _RE_DNI.match(v):
            raise ValueError("El DNI debe tener exactamente 8 dígitos")
        return v


class ConductorUpdate(BaseModel):
    """Datos opcionales para editar la ficha de un conductor (correo no editable aqui)."""
    nombre: Optional[str] = None
    telefono: Optional[str] = None
    dni: Optional[str] = None

    @field_validator("nombre")
    @classmethod
    def _v_nombre(cls, v: Optional[str]) -> Optional[str]:
        if v in (None, ""):
            return None
        v = v.strip()
        if len(v) < 3:
            raise ValueError("El nombre debe tener al menos 3 caracteres")
        return v

    @field_validator("telefono")
    @classmethod
    def _v_telefono(cls, v: Optional[str]) -> Optional[str]:
        if v in (None, ""):
            return None
        v = v.strip().replace(" ", "")
        if not _RE_TELEFONO.match(v):
            raise ValueError("El teléfono debe tener 9 dígitos y empezar en 9")
        return v

    @field_validator("dni")
    @classmethod
    def _v_dni(cls, v: Optional[str]) -> Optional[str]:
        if v in (None, ""):
            return None
        v = v.strip()
        if not _RE_DNI.match(v):
            raise ValueError("El DNI debe tener exactamente 8 dígitos")
        return v


class ConductorResetContrasena(BaseModel):
    """Nueva contrasena definida por el admin para un conductor. Recibe: contrasena."""
    contrasena: str

    @field_validator("contrasena")
    @classmethod
    def _v_contrasena(cls, v: str) -> str:
        return validar_fuerza_contrasena(v)


class UbicacionRequest(BaseModel):
    """Posicion actual reportada por la app del conductor. Recibe: latitud y longitud."""
    latitud: float
    longitud: float


class VehiculoAsignado(BaseModel):
    id: int
    codigo: Optional[str] = None
    placa: str

    class Config:
        from_attributes = True


class ConductorResponse(BaseModel):
    """Ficha del conductor con su vehiculo asignado (si tiene)."""
    usuario_id: int
    codigo: Optional[str] = None
    correo: str
    estado: bool
    en_ruta: bool = False
    solicito_restablecimiento: bool = False
    nombre: Optional[str] = None
    telefono: Optional[str] = None
    dni: Optional[str] = None
    foto_url: Optional[str] = None
    vehiculo: Optional[VehiculoAsignado] = None
