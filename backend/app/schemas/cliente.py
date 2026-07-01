from typing import Optional
from pydantic import BaseModel


class ClienteCreate(BaseModel):
    """Datos para registrar una empresa cliente."""
    razon_social: str
    identificador_unico: Optional[str] = None  # RUC
    contacto: Optional[str] = None
    direccion_origen: str


class ClienteUpdate(BaseModel):
    """Edicion parcial de una empresa cliente; si cambia direccion_origen se re-geocodifica."""
    razon_social: Optional[str] = None
    identificador_unico: Optional[str] = None  # RUC
    contacto: Optional[str] = None
    direccion_origen: Optional[str] = None


class ClienteResponse(BaseModel):
    """Datos de salida de una empresa cliente."""
    id: int
    codigo: Optional[str] = None
    razon_social: str
    identificador_unico: Optional[str] = None
    contacto: Optional[str] = None
    direccion_origen: Optional[str] = None
    distrito: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None

    class Config:
        from_attributes = True
