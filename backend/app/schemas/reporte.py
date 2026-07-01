from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ReporteCreate(BaseModel):
    """Datos para crear un reporte de falla. Recibe pedido_id, motivo y descripcion opcional."""
    pedido_id: int
    motivo: str
    descripcion: Optional[str] = None


class ResponderReporte(BaseModel):
    """Datos para que el admin responda un reporte. Recibe respuesta, accion y estado."""
    respuesta: str
    accion: Optional[str] = None
    estado: Optional[str] = "RESUELTO"  # ABIERTO | RESUELTO


class ReporteResponse(BaseModel):
    """Reporte completo con respuesta del admin si la hay."""
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
