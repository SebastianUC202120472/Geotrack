# app/schemas/almacen.py
# Moldes de datos del módulo de almacén (CUS-14) para la API.
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class ConteoConciliacion(BaseModel):
    """Resumen de conciliación de un recojo (flujo manual, sin escaneo)."""
    esperados: int       # total de pedidos del recojo
    listos: int          # LISTO_PARA_ENVIO (validados, disponibles para ruta)
    observados: int      # OBSERVADO (no llegaron / con discrepancia)
    por_recoger: int     # POR_RECOGER (aún sin procesar en almacén)


# Reusado por el módulo de retornos (CUS-32) para recibir un código escaneado.
class EscaneoRequest(BaseModel):
    """ENTRADA: un código escaneado (retornos)."""
    codigo: str


class PedidoIngresoItem(BaseModel):
    """Un pedido del recojo, para la tabla de ingreso manual del almacén."""
    pedido_id: int
    referencia: str                       # referencia_externa (tracking del cliente)
    codigo: Optional[str] = None          # código interno PD-001
    nombre_destinatario: Optional[str] = None
    direccion_destino: str
    estado: str                           # POR_RECOGER | LISTO_PARA_ENVIO | OBSERVADO


class ConciliacionResponse(BaseModel):
    """SALIDA: conciliación detallada de un recojo + fotos de evidencia del conductor."""
    recojo_id: int
    estado_recojo: str
    conteo: ConteoConciliacion
    pedidos: List[PedidoIngresoItem]
    fotos: List[str]                      # URLs de las fotos que subió el conductor


class RecojoAlmacenItem(BaseModel):
    """Un recojo en la lista del módulo de almacén, con su conteo."""
    id: int
    codigo: Optional[str] = None
    cliente_origen: str
    estado: str
    cantidad_declarada: Optional[int] = None
    conteo: ConteoConciliacion


class ConfirmarIngresoRequest(BaseModel):
    """ENTRADA: referencias (tracking) de los pedidos que NO llegaron (quedan OBSERVADO)."""
    referencias_faltantes: List[str] = []


class ConfirmarIngresoResponse(BaseModel):
    """SALIDA: resultado de confirmar el ingreso (faltantes a OBSERVADO, resto a LISTO_PARA_ENVIO)."""
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
