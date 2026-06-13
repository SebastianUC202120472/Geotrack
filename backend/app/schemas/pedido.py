# app/schemas/pedido.py
# ============================================================================
# CAPA: SCHEMA (validación/serialización con Pydantic) — Clean Architecture
# ----------------------------------------------------------------------------
# ¿QUÉ HACE?  Define los "moldes" de las respuestas del módulo de Pedidos
#             (carga de Excel, geocodificación, listado y agrupación por zonas).
# ¿CON QUÉ SE CONECTA?
#   - Lo USAN: api/pedidos.py (response_model) y services/pedido_service.py.
#   - PedidoResponse refleja las columnas del modelo models/pedido.py.
# ============================================================================
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


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

    class Config:
        from_attributes = True  # se construye directo desde el objeto SQLAlchemy


class CargaPedidosResponse(BaseModel):
    """Resultado de la carga masiva por Excel (CUS-13)."""
    mensaje: str
    pedidos_nuevos: int
    total_filas_leidas: int


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
