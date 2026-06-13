# app/schemas/vehiculo.py
# ============================================================================
# CAPA: SCHEMA (Pydantic) — Vehículos
# ----------------------------------------------------------------------------
# ¿QUÉ HACE?  Moldes de entrada/salida del módulo de vehículos.
# ¿CON QUÉ SE CONECTA?  api/vehiculos.py y services/vehiculo_service.py.
# ============================================================================
from typing import Optional
from pydantic import BaseModel


class VehiculoCreate(BaseModel):
    """ENTRADA: datos para registrar un vehículo."""
    placa: str
    marca: Optional[str] = None
    capacidad_volumetrica: Optional[float] = None
    estado: Optional[str] = "DISPONIBLE"
    conductor_id: Optional[int] = None  # dueño/asignado; None = de la empresa


class VehiculoResponse(BaseModel):
    """SALIDA: datos de un vehículo."""
    id: int
    codigo: Optional[str] = None  # VE-001
    placa: str
    marca: Optional[str] = None
    capacidad_volumetrica: Optional[float] = None
    estado: str
    conductor_id: Optional[int] = None

    class Config:
        from_attributes = True
