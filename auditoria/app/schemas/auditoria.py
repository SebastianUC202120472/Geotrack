from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class DictamenIn(BaseModel):
    dictamen: Literal["VALIDA", "OBSERVADA"]
    motivo: Optional[str] = Field(default=None, max_length=500)


class RevisionOut(BaseModel):
    id: int
    admin_id: int
    admin_email: str
    dictamen: str
    motivo: Optional[str] = None
    registrado_en: datetime


class ReclamoResumenOut(BaseModel):
    id: int
    codigo: Optional[str] = None
    tipo: str
    detalle: str
    creado_en: Optional[datetime] = None


class EvidenciaResumenOut(BaseModel):
    id: int
    evidencia_id: int
    pedido_id: int
    pedido_codigo: Optional[str] = None
    direccion_destino: Optional[str] = None
    pedido_distrito: Optional[str] = None
    conductor_id: Optional[int] = None
    conductor_nombre: Optional[str] = None
    semaforo: str
    motivo_alerta: Optional[str] = None
    estado_revision: str
    calidad_score: float
    es_duplicada: bool
    vision_analizada: bool
    vision_explicacion: Optional[str] = None
    tiene_reclamo: bool = False
    reclamos_count: int = 0
    fecha_entrega: Optional[datetime] = None
    creado_en: datetime


class EvidenciaDetalleOut(EvidenciaResumenOut):
    es_borrosa: bool
    varianza_laplaciana: Optional[float] = None
    es_oscura: bool
    es_sobreexpuesta: bool
    brillo_promedio: Optional[float] = None
    resolucion_ancho: Optional[int] = None
    resolucion_alto: Optional[int] = None
    tiene_exif: bool
    exif_fecha: Optional[datetime] = None
    distancia_gps_metros: Optional[float] = None
    desfase_temporal_minutos: Optional[float] = None
    alerta_gps: bool
    alerta_fecha: bool
    duplicada_con_evidencia_id: Optional[int] = None
    distancia_hamming: Optional[int] = None
    vision_paquete: Optional[bool] = None
    vision_fachada: Optional[bool] = None
    vision_persona: Optional[bool] = None
    vision_texto_sospechoso: Optional[bool] = None
    vision_proveedor: Optional[str] = None
    receptor_nombre: Optional[str] = None
    receptor_documento: Optional[str] = None
    latitud_longitud_captura: Optional[str] = None
    reclamos: List[ReclamoResumenOut] = []
    revisiones: List[RevisionOut] = []


class ReincidenciaConductorOut(BaseModel):
    conductor_id: Optional[int] = None
    conductor_nombre: str
    total_analizadas: int
    total_observadas: int
    total_alertas_rojas: int
    porcentaje_observadas: float


class MetricasOut(BaseModel):
    total_analizadas: int
    total_verde: int
    total_ambar: int
    total_rojo: int
    pendientes_revision: int
    total_revisadas: int
    total_observadas: int
    porcentaje_observadas: float
    falsas_alarmas: int
    tasa_falsas_alarmas: float
    reincidencia_conductores: List[ReincidenciaConductorOut]
