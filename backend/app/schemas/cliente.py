# app/schemas/cliente.py
# Moldes de entrada/salida del módulo de Clientes Corporativos.
from typing import Optional
from pydantic import BaseModel


class ClienteCreate(BaseModel):
    """ENTRADA: datos para registrar una empresa cliente."""
    razon_social: str
    identificador_unico: Optional[str] = None  # RUC
    contacto: Optional[str] = None


class ClienteUpdate(BaseModel):
    """ENTRADA: edición de una empresa cliente. Todos los campos son opcionales."""
    razon_social: Optional[str] = None
    identificador_unico: Optional[str] = None  # RUC
    contacto: Optional[str] = None


class ClienteResponse(BaseModel):
    """SALIDA: datos de una empresa cliente."""
    id: int
    codigo: Optional[str] = None  # CL-001
    razon_social: str
    identificador_unico: Optional[str] = None
    contacto: Optional[str] = None

    class Config:
        from_attributes = True
