# app/schemas/almacen.py
# Moldes de datos del módulo de almacén (CUS-14) para la API.
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class ConteoConciliacion(BaseModel):
    """Resumen de conciliación de un recojo."""
    esperados: int
    ingresados: int
    faltantes: int
    desconocidos: int


class TramaImportResponse(BaseModel):
    """SALIDA: resultado de importar la trama de un recojo."""
    recojo_id: int
    importados: int
    duplicados: int
    total_trama: int
    mensaje: str


class EscaneoRequest(BaseModel):
    """ENTRADA: un código escaneado."""
    codigo: str


class EscaneoResponse(BaseModel):
    """SALIDA: resultado de cruzar un escaneo contra la trama."""
    resultado: str  # INGRESADO | DUPLICADO | DESCONOCIDO
    codigo: str
    mensaje: str
    conteo: ConteoConciliacion


class PaqueteEsperadoItem(BaseModel):
    """Una fila de la trama, para listarla en el panel."""
    codigo: str
    estado: str
    escaneado_en: Optional[datetime] = None


class ConciliacionResponse(BaseModel):
    """SALIDA: conciliación detallada de un recojo."""
    recojo_id: int
    estado_recojo: str
    conteo: ConteoConciliacion
    esperados: List[PaqueteEsperadoItem]
    desconocidos: List[str]


class RecojoAlmacenItem(BaseModel):
    """Un recojo en la lista del módulo de almacén, con su conteo."""
    id: int
    codigo: Optional[str] = None
    cliente_origen: str
    estado: str
    cantidad_declarada: Optional[int] = None
    conteo: ConteoConciliacion


class CerrarIngresoResponse(BaseModel):
    """SALIDA: resultado de cerrar el ingreso de un recojo."""
    recojo_id: int
    estado: str
    conteo: ConteoConciliacion
    mensaje: str
