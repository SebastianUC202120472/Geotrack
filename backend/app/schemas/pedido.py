# app/schemas/pedido.py
# Define los "moldes" de las respuestas del módulo de Pedidos (carga de Excel, geocodificación, listado y agrupación por zonas).
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class PedidoResponse(BaseModel):
    """Molde de SALIDA de un pedido (todas sus columnas)."""
    id: int
    codigo: Optional[str] = None            # PD-001 (tracking real / QR)
    referencia_externa: Optional[str] = None  # id que vino en el Excel (opcional)
    cliente_id: Optional[int] = None        # empresa que envía (FK a clientes_corporativos)
    cliente_origen: str                     # nombre del cliente (snapshot)
    direccion_destino: str
    # Datos del destinatario (quién recibe) — Fase 4
    nombre_destinatario: Optional[str] = None
    telefono_destinatario: Optional[str] = None
    dni_destinatario: Optional[str] = None
    distrito: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    peso_kg: Optional[float] = None
    volumen_m3: Optional[float] = None
    estado: str
    fecha_creacion: Optional[datetime] = None
    fecha_entrega: Optional[datetime] = None
    # Provenance de recojo (Task 3)
    recojo_id: Optional[int] = None       # solicitud de recojo de la que salió este pedido
    validado_en: Optional[datetime] = None  # momento en que fue validado en almacén
    # Asignación (se completan al listar; no son columnas del pedido)
    ruta_nombre: Optional[str] = None
    conductor_nombre: Optional[str] = None

    class Config:
        from_attributes = True  # se construye directo desde el objeto SQLAlchemy


class CargaPedidosResponse(BaseModel):
    """Resultado de la carga masiva por Excel (CUS-13).

    La geocodificación (CUS-15) ahora corre dentro de la misma carga, por eso
    también informamos cuántos pedidos quedaron con coordenadas y cuántos no.
    """
    mensaje: str
    pedidos_nuevos: int
    total_filas_leidas: int
    pedidos_geocodificados: int = 0
    pedidos_fallidos: int = 0
    rechazados: List[dict] = []        # filas no importadas por cliente no registrado
    total_rechazados: int = 0


class GeocodificacionResponse(BaseModel):
    """Resultado del proceso de geocodificación (CUS-15)."""
    mensaje: str
    pedidos_exitosos: int = 0
    pedidos_fallidos: int = 0


class ZonaItem(BaseModel):
    """Una zona operativa: distrito + cantidad de pedidos."""
    distrito: Optional[str] = None
    total_pedidos: int


class ZonasResponse(BaseModel):
    """Agrupación de pedidos por distrito (CUS-16)."""
    zonas_operativas: List[ZonaItem]


# --- CUS-17: resolución manual de direcciones ---
class UbicacionManualRequest(BaseModel):
    """ENTRADA (CUS-17): el admin fija a mano la ubicación de un pedido. La dirección
    es opcional (por si la corrige al ubicarla en el mapa). Se valida que las
    coordenadas estén en rango y no sean NaN/Infinity."""
    model_config = ConfigDict(allow_inf_nan=False)

    latitud: float = Field(ge=-90, le=90)
    longitud: float = Field(ge=-180, le=180)
    direccion: Optional[str] = None


class BuscarDireccionResponse(BaseModel):
    """SALIDA (CUS-17): resultado de geocodificar un texto de búsqueda en el mapa."""
    encontrado: bool
    latitud: Optional[float] = None
    longitud: Optional[float] = None
