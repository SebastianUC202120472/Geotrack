from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class ConteoConciliacion(BaseModel):
    """Conteo de estados de pedidos en un recojo."""
    esperados: int
    listos: int
    observados: int
    por_recoger: int


class EscaneoRequest(BaseModel):
    """Recibe un codigo escaneado."""
    codigo: str


class PedidoIngresoItem(BaseModel):
    """Pedido del recojo para la tabla de ingreso manual."""
    pedido_id: int
    referencia: str
    codigo: Optional[str] = None
    nombre_destinatario: Optional[str] = None
    direccion_destino: str
    estado: str


class ConciliacionResponse(BaseModel):
    """Conciliacion detallada de un recojo con pedidos y fotos."""
    recojo_id: int
    estado_recojo: str
    conteo: ConteoConciliacion
    pedidos: List[PedidoIngresoItem]
    fotos: List[str]


class RecojoAlmacenItem(BaseModel):
    """Recojo en la lista del modulo de almacen con su conteo."""
    id: int
    codigo: Optional[str] = None
    cliente_origen: str
    estado: str
    cantidad_declarada: Optional[int] = None
    conteo: ConteoConciliacion


class ConfirmarIngresoRequest(BaseModel):
    """Recibe referencias de pedidos faltantes para marcarlos OBSERVADO."""
    referencias_faltantes: List[str] = []


class ConfirmarIngresoResponse(BaseModel):
    """Resultado de confirmar el ingreso de un recojo."""
    recojo_id: int
    estado: str
    conteo: ConteoConciliacion
    mensaje: str


class ConteoRetorno(BaseModel):
    """Conteo de paquetes FALLIDO en el retorno de una ruta."""
    esperados: int
    retornados: int
    faltantes: int


class RutaRetornoItem(BaseModel):
    """Ruta de entrega con pedidos FALLIDO en la lista de retornos."""
    ruta_id: int
    codigo: Optional[str] = None
    nombre: str
    estado: str
    conteo: ConteoRetorno


class FallidoItem(BaseModel):
    """Pedido FALLIDO de la ruta con datos de retorno."""
    pedido_id: int
    codigo: Optional[str] = None
    cliente_origen: str
    direccion_destino: str
    nombre_destinatario: Optional[str] = None
    retornado_en: Optional[datetime] = None


class RetornoRutaResponse(BaseModel):
    """Detalle del retorno de una ruta con lista de FALLIDO."""
    ruta_id: int
    codigo: Optional[str] = None
    nombre: str
    conteo: ConteoRetorno
    fallidos: List[FallidoItem]


class EscaneoRetornoResponse(BaseModel):
    """Resultado de escanear un paquete devuelto."""
    resultado: str
    codigo: str
    mensaje: str
    conteo: ConteoRetorno
