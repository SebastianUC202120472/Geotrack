from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, field_validator


# Waypoint para el mapa de navegación.
class ParadaNavegacion(BaseModel):
    secuencia: int
    pedido_id: int
    codigo: Optional[str] = None
    latitud: float
    longitud: float


# Parada completa del manifiesto de entrega.
class ParadaManifiesto(BaseModel):
    secuencia: int
    detalle_id: int
    pedido_id: int
    codigo: Optional[str] = None
    cliente_origen: str
    nombre_destinatario: Optional[str] = None
    telefono_destinatario: Optional[str] = None
    direccion_destino: str
    distrito: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    peso_kg: Optional[float] = None
    estado_entrega: str  # PENDIENTE, ENTREGADO, FALLIDO
    url_evidencia: Optional[str] = None


# Resumen de la ruta activa del conductor.
class RutaActivaResponse(BaseModel):
    ruta_id: int
    codigo: Optional[str] = None
    nombre: str
    estado: str  # CREADA, EN_PROGRESO
    fecha_creacion: datetime
    fecha_salida: Optional[datetime] = None
    vehiculo_placa: Optional[str] = None
    total_paradas: int
    pendientes: int
    entregadas: int
    fallidas: int
    pausada: bool = False  # True si hay incidencia abierta (auxilio mecánico)
    incidencia_id: Optional[int] = None
    ayuda_enviada_en: Optional[datetime] = None
    ayuda_detalle: Optional[str] = None
    tipo: str = "ENTREGA"  # ENTREGA (outbound) | RECOJO (inbound)


# Manifiesto completo y ordenado de la ruta.
class ManifiestoResponse(BaseModel):
    ruta_id: int
    codigo: Optional[str] = None
    nombre: str
    estado: str
    total_paradas: int
    paradas: List[ParadaManifiesto]


# Secuencia de navegación para el mapa.
class NavegacionResponse(BaseModel):
    ruta_id: int
    total_paradas: int
    paradas: List[ParadaNavegacion]


# Solicitud para actualizar el estado de una parada. Recibe estado y motivo opcional.
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
    codigo: Optional[str] = None
    estado_entrega: str
    motivo_fallo: Optional[str] = None
    url_evidencia: Optional[str] = None
    fecha_gestion: Optional[datetime] = None
    mensaje: str


class CierreRutaResponse(BaseModel):
    ruta_id: int
    codigo: Optional[str] = None
    nombre: str
    estado: str
    fecha_fin: Optional[datetime] = None
    hora_inicio: Optional[datetime] = None
    hora_fin: Optional[datetime] = None
    duracion_minutos: Optional[int] = None
    total_paradas: int
    entregadas: int
    fallidas: int
    pendientes: int
    mensaje: str


# Solicitud para asignar un bloque de pedidos a una ruta. Recibe distrito y conductor.
class AsignacionBloqueRequest(BaseModel):
    """Arma una ruta con pedidos de un distrito. nombre_ruta opcional; si se omite se genera desde la zona."""
    nombre_ruta: Optional[str] = None
    distrito: str
    conductor_id: int


class AsignacionBloqueResponse(BaseModel):
    """Confirmacion de la ruta creada con su id y codigo."""
    mensaje: str
    ruta_id: int
    codigo: Optional[str] = None


class OptimizacionRequest(BaseModel):
    """Solicitud de optimizacion de ruta desde la posicion actual del conductor."""
    ruta_id: int
    latitud_actual_conductor: float
    longitud_actual_conductor: float


class OptimizacionResponse(BaseModel):
    """Confirmacion de optimizacion con el total de paradas reordenadas."""
    mensaje: str
    total_paradas: int


# Parada de la ruta vista por el admin para reordenar o quitar.
class ParadaAdmin(BaseModel):
    secuencia: int
    pedido_id: int
    codigo: Optional[str] = None
    cliente_origen: str
    nombre_destinatario: Optional[str] = None
    direccion_destino: str
    distrito: Optional[str] = None
    estado_entrega: str


# Ruta con paradas ordenadas para edicion en el panel.
class RutaParadasResponse(BaseModel):
    ruta_id: int
    codigo: Optional[str] = None
    nombre: str
    estado: str
    total_paradas: int
    paradas: List[ParadaAdmin]


# Nuevo orden de paradas. Recibe lista de pedido_id en orden deseado.
class ReordenarRequest(BaseModel):
    orden: List[int]
