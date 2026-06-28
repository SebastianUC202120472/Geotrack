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


# --- CUS-32: retorno a almacén (logística inversa) ---
class ConteoRetorno(BaseModel):
    """Resumen de conciliación del retorno de una ruta."""
    esperados: int    # paquetes FALLIDO de la ruta
    retornados: int   # FALLIDO ya escaneados de vuelta
    faltantes: int    # FALLIDO que no regresaron


class RutaRetornoItem(BaseModel):
    """Una ruta de entrega con FALLIDO, en la lista de retornos."""
    ruta_id: int
    codigo: Optional[str] = None
    nombre: str
    estado: str
    conteo: ConteoRetorno


class FallidoItem(BaseModel):
    """Un paquete FALLIDO de la ruta, con su estado de retorno."""
    pedido_id: int
    codigo: Optional[str] = None
    cliente_origen: str
    direccion_destino: str
    nombre_destinatario: Optional[str] = None
    retornado_en: Optional[datetime] = None


class RetornoRutaResponse(BaseModel):
    """SALIDA: detalle del retorno de una ruta (FALLIDO + conteo)."""
    ruta_id: int
    codigo: Optional[str] = None
    nombre: str
    conteo: ConteoRetorno
    fallidos: List[FallidoItem]


class EscaneoRetornoResponse(BaseModel):
    """SALIDA: resultado de escanear un paquete devuelto."""
    resultado: str  # RETORNADO | DUPLICADO | DESCONOCIDO
    codigo: str
    mensaje: str
    conteo: ConteoRetorno
