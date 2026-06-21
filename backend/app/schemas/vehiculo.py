# app/schemas/vehiculo.py
# Moldes de entrada/salida del módulo de vehículos.
import re
from typing import Optional
from pydantic import BaseModel, field_validator

# Placa estándar de auto en Perú: 3 letras + 3 dígitos (ej. ABC-123).
_RE_PLACA = re.compile(r"^[A-Z]{3}-\d{3}$")


def _validar_capacidad_m3(v: Optional[float]) -> Optional[float]:
    """Valida la capacidad volumétrica (m³): mayor a 0 y máximo 100. Recibe: el valor."""
    if v is None:
        return v
    if v <= 0:
        raise ValueError("La capacidad debe ser mayor a 0")
    if v > 100:
        raise ValueError("La capacidad es demasiado alta (máximo 100 m³)")
    return v


def _validar_capacidad_cajas(v: Optional[int]) -> Optional[int]:
    """Valida la capacidad en cajas (entero positivo razonable). Recibe: el valor."""
    if v is None:
        return v
    if v <= 0:
        raise ValueError("La capacidad en cajas debe ser mayor a 0")
    if v > 100000:
        raise ValueError("La capacidad en cajas es demasiado alta")
    return v


class VehiculoCreate(BaseModel):
    """ENTRADA: datos para registrar un vehículo."""
    placa: str
    marca: Optional[str] = None
    capacidad_volumetrica: Optional[float] = None
    capacidad_cajas: Optional[int] = None  # CUS-08: cuántas cajas soporta
    estado: Optional[str] = "DISPONIBLE"
    conductor_id: Optional[int] = None  # dueño/asignado; None = de la empresa

    @field_validator("placa")
    @classmethod
    def _v_placa(cls, v: str) -> str:
        # Normaliza "abc123"/"ABC 123" -> "ABC-123" y valida el formato.
        v = (v or "").strip().upper().replace(" ", "").replace("-", "")
        if len(v) == 6 and v[:3].isalpha() and v[3:].isdigit():
            v = f"{v[:3]}-{v[3:]}"
        if not _RE_PLACA.match(v):
            raise ValueError("Placa inválida. Usa el formato peruano de 3 letras y 3 dígitos (ej. ABC-123)")
        return v

    @field_validator("capacidad_volumetrica")
    @classmethod
    def _v_capacidad(cls, v: Optional[float]) -> Optional[float]:
        return _validar_capacidad_m3(v)

    @field_validator("capacidad_cajas")
    @classmethod
    def _v_cajas(cls, v: Optional[int]) -> Optional[int]:
        return _validar_capacidad_cajas(v)


class VehiculoUpdate(BaseModel):
    """ENTRADA (CUS-08/09): edición de un vehículo. Todos los campos son opcionales:
    marca/capacidades para editar, conductor_id para (re)asignar (None lo desvincula)."""
    marca: Optional[str] = None
    capacidad_volumetrica: Optional[float] = None
    capacidad_cajas: Optional[int] = None
    conductor_id: Optional[int] = None

    @field_validator("capacidad_volumetrica")
    @classmethod
    def _v_capacidad(cls, v: Optional[float]) -> Optional[float]:
        return _validar_capacidad_m3(v)

    @field_validator("capacidad_cajas")
    @classmethod
    def _v_cajas(cls, v: Optional[int]) -> Optional[int]:
        return _validar_capacidad_cajas(v)


class VehiculoResponse(BaseModel):
    """SALIDA: datos de un vehículo."""
    id: int
    codigo: Optional[str] = None  # VE-001
    placa: str
    marca: Optional[str] = None
    capacidad_volumetrica: Optional[float] = None
    capacidad_cajas: Optional[int] = None
    estado: str
    conductor_id: Optional[int] = None

    class Config:
        from_attributes = True
