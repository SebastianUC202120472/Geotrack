import re
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator

# Prefijos validos del RUC peruano: 10 persona natural, 15/16/17 casos especiales, 20 empresa.
_PREFIJOS_RUC = ("10", "15", "16", "17", "20")
_PESOS_RUC = (5, 4, 3, 2, 7, 6, 5, 4, 3, 2)


def normalizar_ruc(v: Optional[str]) -> Optional[str]:
    """Valida el formato del RUC (11 digitos con prefijo valido) y lo devuelve limpio. Recibe el texto."""
    if v in (None, ""):
        return None
    v = re.sub(r"\s", "", v)
    if not re.fullmatch(r"\d{11}", v):
        raise ValueError("El RUC debe tener exactamente 11 dígitos")
    if not v.startswith(_PREFIJOS_RUC):
        raise ValueError("El RUC debe empezar con 10, 15, 16, 17 o 20")
    return v


def digito_ruc_valido(ruc: str) -> bool:
    """Comprueba el digito verificador del RUC (modulo 11 de SUNAT). Recibe el RUC de 11 digitos."""
    suma = sum(int(d) * p for d, p in zip(ruc[:10], _PESOS_RUC))
    digito = 11 - suma % 11
    digito = {10: 0, 11: 1}.get(digito, digito)
    return digito == int(ruc[10])


def normalizar_razon_social(v: Optional[str]) -> Optional[str]:
    """Quita espacios sobrantes y exige entre 3 y 150 caracteres. Recibe el texto."""
    if v is None:
        return None
    v = " ".join(v.split())
    if len(v) < 3:
        raise ValueError("La razón social debe tener al menos 3 caracteres")
    if len(v) > 150:
        raise ValueError("La razón social no puede superar los 150 caracteres")
    return v


class ClienteCreate(BaseModel):
    """Datos para registrar una empresa cliente."""
    razon_social: str
    identificador_unico: Optional[str] = None  # RUC
    contacto: Optional[str] = None
    direccion_origen: str

    @field_validator("razon_social")
    @classmethod
    def _v_razon(cls, v: str) -> str:
        return normalizar_razon_social(v)

    @field_validator("identificador_unico")
    @classmethod
    def _v_ruc(cls, v: Optional[str]) -> Optional[str]:
        return normalizar_ruc(v)

    @field_validator("direccion_origen")
    @classmethod
    def _v_direccion(cls, v: str) -> str:
        v = (v or "").strip()
        if len(v) < 5:
            raise ValueError("Escribe la dirección de recojo completa")
        return v


class ClienteUpdate(BaseModel):
    """Edicion parcial de una empresa cliente; si cambia direccion_origen se re-geocodifica."""
    razon_social: Optional[str] = None
    identificador_unico: Optional[str] = None  # RUC
    contacto: Optional[str] = None
    direccion_origen: Optional[str] = None

    @field_validator("razon_social")
    @classmethod
    def _v_razon(cls, v: Optional[str]) -> Optional[str]:
        return normalizar_razon_social(v)

    @field_validator("identificador_unico")
    @classmethod
    def _v_ruc(cls, v: Optional[str]) -> Optional[str]:
        return normalizar_ruc(v)


class UbicacionClienteIn(BaseModel):
    """Punto de recojo elegido a mano en el mapa. Recibe latitud y longitud (dentro del Peru)."""
    latitud: float
    longitud: float

    @field_validator("latitud")
    @classmethod
    def _v_lat(cls, v: float) -> float:
        if not -18.5 <= v <= 0.1:
            raise ValueError("La latitud está fuera del Perú")
        return v

    @field_validator("longitud")
    @classmethod
    def _v_lng(cls, v: float) -> float:
        if not -81.5 <= v <= -68.5:
            raise ValueError("La longitud está fuera del Perú")
        return v


class AccesoPortalIn(BaseModel):
    """Datos para generar/reiniciar el acceso al portal de un cliente."""
    correoPortal: EmailStr


class ClienteResponse(BaseModel):
    """Datos de salida de una empresa cliente, con el estado de su acceso al portal."""
    id: int
    codigo: Optional[str] = None
    razon_social: str
    identificador_unico: Optional[str] = None
    contacto: Optional[str] = None
    direccion_origen: Optional[str] = None
    distrito: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    acceso_activo: Optional[bool] = False
    codigo_acceso: Optional[str] = None
    correo_portal: Optional[str] = None

    class Config:
        from_attributes = True
