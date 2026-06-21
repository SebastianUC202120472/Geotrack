# app/schemas/parametro.py
# Moldes del catálogo de parámetros (CUS-06). Por ahora, motivos de rechazo.
from pydantic import BaseModel, field_validator


class MotivoCreate(BaseModel):
    """ENTRADA (CUS-06): alta de un motivo de rechazo."""
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
    """SALIDA (CUS-06): un motivo de rechazo del catálogo."""
    id: int
    texto: str


class CombustibleConfig(BaseModel):
    """Parámetros de combustible (CUS-34), editables desde el panel."""
    consumo_l_100km: float
    precio_soles_litro: float
