# app/schemas/cliente.py
# Moldes de entrada/salida del módulo de Clientes Corporativos.
from typing import Optional
from pydantic import BaseModel


class ClienteCreate(BaseModel):
    """ENTRADA: datos para registrar una empresa cliente."""
    razon_social: str
    identificador_unico: Optional[str] = None  # RUC
    contacto: Optional[str] = None
    direccion_origen: str                       # dirección del almacén/tienda del cliente (requerida)


class ClienteUpdate(BaseModel):
    """ENTRADA: edición de una empresa cliente. Todos los campos son opcionales."""
    razon_social: Optional[str] = None
    identificador_unico: Optional[str] = None  # RUC
    contacto: Optional[str] = None
    direccion_origen: Optional[str] = None      # dirección del punto de recojo; si cambia, se re-geocodifica


class ClienteResponse(BaseModel):
    """SALIDA: datos de una empresa cliente."""
    id: int
    codigo: Optional[str] = None  # CL-001
    razon_social: str
    identificador_unico: Optional[str] = None
    contacto: Optional[str] = None
    direccion_origen: Optional[str] = None
    distrito: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None

    class Config:
        from_attributes = True
