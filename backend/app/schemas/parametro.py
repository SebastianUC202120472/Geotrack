import re
from typing import Optional

from pydantic import BaseModel, field_validator


class MotivoCreate(BaseModel):
    """Alta de un motivo de rechazo. Recibe texto."""
    texto: str

    @field_validator("texto")
    @classmethod
    def _v_texto(cls, v: str) -> str:
        v = (v or "").strip()
        if len(v) < 3:
            raise ValueError("El motivo debe tener al menos 3 caracteres")
        if len(v) > 120:
            raise ValueError("El motivo es demasiado largo (máximo 120 caracteres)")
        return v


class MotivoResponse(BaseModel):
    """Respuesta con un motivo de rechazo del catálogo."""
    id: int
    texto: str


class CombustibleConfig(BaseModel):
    """Parámetros de combustible editables desde el panel."""
    consumo_l_100km: float
    precio_soles_litro: float


class ContactoConfig(BaseModel):
    """Telefono de coordinacion que la app muestra en Ayuda y Reportar un error (EX-13)."""
    telefono_coordinacion: Optional[str] = None

    @field_validator("telefono_coordinacion")
    @classmethod
    def _v_telefono(cls, v: Optional[str]) -> Optional[str]:
        v = " ".join((v or "").split())
        if not v:
            return None
        digitos = re.sub(r"\D", "", v)
        if not re.fullmatch(r"\+?[\d ]+", v) or not 7 <= len(digitos) <= 15:
            raise ValueError("Escribe un teléfono válido (solo números, con + y código de país si quieres)")
        return v
