from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class ReporteCreate(BaseModel):
    """Datos para crear un reporte de falla. Recibe pedido_id, motivo y descripcion opcional."""
    pedido_id: int
    motivo: str
    descripcion: Optional[str] = None


class ResponderReporte(BaseModel):
    """Respuesta del admin y su decision sobre el pedido (C31-01). Recibe respuesta, accion
    (REPROGRAMAR | CANCELAR | NINGUNA), motivo de cancelacion y estado."""
    respuesta: str
    accion: Optional[str] = "NINGUNA"
    motivo_cancelacion: Optional[str] = Field(None, max_length=255)
    estado: Optional[str] = "RESUELTO"  # ABIERTO | RESUELTO

    @field_validator("accion")
    @classmethod
    def validar_accion(cls, v: Optional[str]) -> str:
        v = (v or "NINGUNA").strip().upper()
        if v not in ("REPROGRAMAR", "CANCELAR", "NINGUNA"):
            raise ValueError("La acción debe ser REPROGRAMAR, CANCELAR o NINGUNA")
        return v


class ReporteResponse(BaseModel):
    """Reporte completo con respuesta del admin si la hay."""
    id: int
    pedido_id: int
    pedido_codigo: Optional[str] = None
    direccion_destino: Optional[str] = None  # se completa al listar (no es columna)
    pedido_estado: Optional[str] = None      # para saber si aun se puede decidir
    conductor_id: int
    conductor_nombre: Optional[str] = None
    motivo: str
    descripcion: Optional[str] = None
    estado: str
    respuesta: Optional[str] = None
    accion: Optional[str] = None
    creado_en: Optional[datetime] = None
    respondido_en: Optional[datetime] = None
    url_evidencia: Optional[str] = None             # foto que respalda la falla (C29-01)
    latitud_longitud_captura: Optional[str] = None  # "lat,lng" donde se tomo
