# app/schemas/reporte.py
# Moldes de los reportes de incidencia (conductor crea; admin responde).
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ReporteCreate(BaseModel):
    """ENTRADA (conductor): reporta la falla de un pedido."""
    pedido_id: int
    motivo: str
    descripcion: Optional[str] = None


class ResponderReporte(BaseModel):
    """ENTRADA (admin): responde un reporte con la solución."""
    respuesta: str
    accion: Optional[str] = None
    estado: Optional[str] = "RESUELTO"  # ABIERTO | RESUELTO


class ReporteResponse(BaseModel):
    """SALIDA: el reporte con sus datos y la respuesta del admin si la hay."""
    id: int
    pedido_id: int
    pedido_codigo: Optional[str] = None
    direccion_destino: Optional[str] = None  # se completa al listar (no es columna)
    conductor_id: int
    conductor_nombre: Optional[str] = None
    motivo: str
    descripcion: Optional[str] = None
    estado: str
    respuesta: Optional[str] = None
    accion: Optional[str] = None
    creado_en: Optional[datetime] = None
    respondido_en: Optional[datetime] = None
