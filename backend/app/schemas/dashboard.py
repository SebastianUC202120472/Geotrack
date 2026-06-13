# app/schemas/dashboard.py
# Define los "moldes" de salida del módulo de TRAZABILIDAD (Fase 4).
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel


# CUS-33: Seguimiento en vivo de la flota
class RutaFlota(BaseModel):
    """Estado y avance de UNA ruta dentro del dashboard de flota."""
    ruta_id: int
    nombre: str
    estado: str  # CREADA, EN_PROGRESO, FINALIZADA
    conductor_id: Optional[int] = None
    conductor_correo: Optional[str] = None
    vehiculo_placa: Optional[str] = None
    total_paradas: int
    entregadas: int
    fallidas: int
    pendientes: int
    avance_porcentaje: float  # % de paradas ya gestionadas (entregadas + fallidas)
    fecha_creacion: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None


class FlotaResponse(BaseModel):
    """Listado completo de rutas para el tablero de la flota."""
    total_rutas: int
    rutas: List[RutaFlota]


class ResumenResponse(BaseModel):
    """KPIs globales del día (tarjetas del dashboard)."""
    total_pedidos: int
    pedidos_por_estado: Dict[str, int]  # ej. {"PENDIENTE": 2, "ENTREGADO": 3}
    total_rutas: int
    rutas_activas: int
    rutas_finalizadas: int


# CUS-35: Historial / línea de tiempo de un paquete
class EventoHistorial(BaseModel):
    """Un punto en la línea de tiempo del paquete (fila de historial_pedidos)."""
    evento: str                       # estado al que cambió (ej. "ENTREGADO")
    descripcion: str                  # explicación legible
    fecha: Optional[datetime] = None  # cuándo ocurrió
    realizado_por: Optional[str] = None  # correo del usuario que hizo el cambio


class HistorialPedidoResponse(BaseModel):
    """Trazabilidad completa de un paquete (CUS-35)."""
    codigo: Optional[str] = None  # PD-001
    cliente_origen: str
    direccion_destino: str
    distrito: Optional[str] = None
    estado_actual: str
    ruta_asignada: Optional[str] = None
    conductor_asignado: Optional[str] = None  # nombre del conductor de la ruta
    secuencia: Optional[int] = None
    url_evidencia: Optional[str] = None
    motivo_fallo: Optional[str] = None
    eventos: List[EventoHistorial]  # la línea de tiempo, en orden cronológico
