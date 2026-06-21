# app/schemas/conductor.py
# Moldes para registrar un conductor (con sus datos) y para listarlos junto al vehículo que tienen asignado.
import re
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator

# Reglas (estándar Perú): celular = 9 dígitos empezando en 9; DNI = 8 dígitos.
_RE_TELEFONO = re.compile(r"^9\d{8}$")
_RE_DNI = re.compile(r"^\d{8}$")


class ConductorCreate(BaseModel):
    """ENTRADA: alta de un conductor (crea su cuenta + su ficha)."""
    correo: EmailStr            # EmailStr valida el formato del correo
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
        # Contraseña segura (se guardará hasheada): mínimo 8, con mayúscula,
        # minúscula y número.
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
    """ENTRADA: edición de la ficha de un conductor. Todos los campos son
    opcionales; el correo (acceso) NO se edita aquí."""
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


class UbicacionRequest(BaseModel):
    """ENTRADA: la app del conductor reporta su posición actual (foreground)."""
    latitud: float
    longitud: float


class VehiculoAsignado(BaseModel):
    id: int
    codigo: Optional[str] = None
    placa: str

    class Config:
        from_attributes = True


class ConductorResponse(BaseModel):
    """SALIDA: ficha del conductor + su vehículo asignado (si tiene)."""
    usuario_id: int
    codigo: Optional[str] = None   # CO-001
    correo: str
    estado: bool
    nombre: Optional[str] = None
    telefono: Optional[str] = None
    dni: Optional[str] = None
    foto_url: Optional[str] = None   # URL pública de la foto (o None si no tiene)
    vehiculo: Optional[VehiculoAsignado] = None
