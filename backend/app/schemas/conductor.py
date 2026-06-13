# app/schemas/conductor.py
# ============================================================================
# CAPA: SCHEMA (Pydantic) — Conductores
# ----------------------------------------------------------------------------
# Moldes para registrar un conductor (con sus datos) y para listarlos junto al
# vehículo que tienen asignado.
# ============================================================================
from typing import Optional
from pydantic import BaseModel, EmailStr


class ConductorCreate(BaseModel):
    """ENTRADA: alta de un conductor (crea su cuenta + su ficha)."""
    correo: EmailStr
    contrasena: str
    nombre: str
    telefono: Optional[str] = None
    dni: Optional[str] = None


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
    vehiculo: Optional[VehiculoAsignado] = None
