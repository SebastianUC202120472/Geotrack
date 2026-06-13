# app/schemas/ruta.py
# Define los "moldes" de datos de RUTAS para la API.
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, field_validator


# --- CUS-25: punto de navegación (waypoint para el mapa) ---
class ParadaNavegacion(BaseModel):
    secuencia: int
    pedido_id: int
    codigo: Optional[str] = None  # PD-001
    latitud: float
    longitud: float


# --- CUS-24: parada completa del manifiesto ---
class ParadaManifiesto(BaseModel):
    secuencia: int
    detalle_id: int
    pedido_id: int
    codigo: Optional[str] = None  # PD-001 (lo que va en el QR)
    cliente_origen: str  # empresa que envía (snapshot)
    nombre_destinatario: Optional[str] = None    # persona que recibe
    telefono_destinatario: Optional[str] = None  # para coordinar la entrega
    direccion_destino: str
    distrito: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    peso_kg: Optional[float] = None
    estado_entrega: str  # PENDIENTE, ENTREGADO, FALLIDO


# --- CUS-21: resumen de la ruta activa del conductor ---
class RutaActivaResponse(BaseModel):
    ruta_id: int
    codigo: Optional[str] = None  # RT-001
    nombre: str
    estado: str  # CREADA, EN_PROGRESO
    fecha_creacion: datetime
    vehiculo_placa: Optional[str] = None
    total_paradas: int
    pendientes: int
    entregadas: int
    fallidas: int


# --- CUS-24: manifiesto completo y ordenado ---
class ManifiestoResponse(BaseModel):
    ruta_id: int
    codigo: Optional[str] = None  # RT-001
    nombre: str
    estado: str
    total_paradas: int
    paradas: List[ParadaManifiesto]


# --- CUS-25: secuencia de navegación ---
class NavegacionResponse(BaseModel):
    ruta_id: int
    total_paradas: int
    paradas: List[ParadaNavegacion]


# FASE 3.2: Validación en almacén (CUS-22)
class ValidacionQRRequest(BaseModel):
    codigo: str  # el código PD-001 escaneado del QR


class ValidacionQRResponse(BaseModel):
    pertenece: bool
    mensaje: str
    parada: Optional[ParadaManifiesto] = None


# FASE 3.3: Ejecución y evidencias (CUS-26 / CUS-29)
class ActualizarEstadoRequest(BaseModel):
    estado: str  # ENTREGADO | FALLIDO
    motivo_fallo: Optional[str] = None

    @field_validator("estado")
    @classmethod
    def validar_estado(cls, v: str) -> str:
        permitidos = {"ENTREGADO", "FALLIDO"}
        v = v.upper().strip()
        if v not in permitidos:
            raise ValueError(f"estado debe ser uno de {permitidos}")
        return v


class GestionParadaResponse(BaseModel):
    pedido_id: int
    codigo: Optional[str] = None  # PD-001
    estado_entrega: str
    motivo_fallo: Optional[str] = None
    url_evidencia: Optional[str] = None
    fecha_gestion: Optional[datetime] = None
    mensaje: str


# FASE 3.4: Cierre de operación (CUS-28)
class CierreRutaResponse(BaseModel):
    ruta_id: int
    codigo: Optional[str] = None  # RT-001
    nombre: str
    estado: str
    fecha_fin: Optional[datetime] = None
    total_paradas: int
    entregadas: int
    fallidas: int
    pendientes: int
    mensaje: str


# FASE 2: Enrutamiento básico y VRP (CUS-18 / CUS-19)
class AsignacionBloqueRequest(BaseModel):
    """ENTRADA (CUS-18): el admin pide armar una ruta con un bloque de pedidos."""
    nombre_ruta: str
    distrito: str
    conductor_id: int


class AsignacionBloqueResponse(BaseModel):
    """SALIDA (CUS-18): confirmación con el id y código de la ruta creada."""
    mensaje: str
    ruta_id: int
    codigo: Optional[str] = None  # RT-001


class OptimizacionRequest(BaseModel):
    """ENTRADA (CUS-19): el conductor pide optimizar su ruta desde su posición actual."""
    ruta_id: int
    latitud_actual_conductor: float
    longitud_actual_conductor: float


class OptimizacionResponse(BaseModel):
    """SALIDA (CUS-19): confirmación con el número total de paradas optimizadas."""
    mensaje: str
    total_paradas: int
