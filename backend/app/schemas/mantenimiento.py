# Esquemas Pydantic del modulo de mantenimiento y documentos de la flota (Idea 4).
# Definen los contratos de entrada/salida y las validaciones de datos.
import re
from datetime import date, datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


PATRON_PLACA = re.compile(r"^[A-Z0-9]{3}-[A-Z0-9]{3}$")


class TipoDocumentoEnum(str, Enum):
    SOAT = "SOAT"
    REVISION_TECNICA = "REVISION_TECNICA"
    TARJETA_CIRCULACION = "TARJETA_CIRCULACION"
    SEGURO = "SEGURO"
    PERMISO_OPERACION = "PERMISO_OPERACION"
    OTRO = "OTRO"


class EstadoDocumentoEnum(str, Enum):
    VIGENTE = "VIGENTE"
    POR_VENCER = "POR_VENCER"
    VENCIDO = "VENCIDO"
    SIN_DOCUMENTO = "SIN_DOCUMENTO"


class TipoMantenimientoEnum(str, Enum):
    PREVENTIVO = "PREVENTIVO"
    CORRECTIVO = "CORRECTIVO"


class EstadoMantenimientoEnum(str, Enum):
    PROGRAMADO = "PROGRAMADO"
    EN_PROCESO = "EN_PROCESO"
    COMPLETADO = "COMPLETADO"
    CANCELADO = "CANCELADO"


class PrioridadMantenimientoEnum(str, Enum):
    BAJA = "BAJA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"


class CategoriaMantenimientoEnum(str, Enum):
    ACEITE = "ACEITE"
    FRENOS = "FRENOS"
    LLANTAS = "LLANTAS"
    MOTOR = "MOTOR"
    SUSPENSION = "SUSPENSION"
    ELECTRICO = "ELECTRICO"
    REVISION_GENERAL = "REVISION_GENERAL"
    OTRO = "OTRO"


class TipoCombustibleEnum(str, Enum):
    DIESEL = "DIESEL"
    GASOLINA_95 = "GASOLINA_95"
    GASOLINA_90 = "GASOLINA_90"
    GLP = "GLP"


class EstadoPreventivoEnum(str, Enum):
    AL_DIA = "AL_DIA"
    PROXIMO = "PROXIMO"
    VENCIDO = "VENCIDO"
    SIN_LECTURAS = "SIN_LECTURAS"


def _normalizar_placa(valor: str) -> str:
    """Pasa la placa a mayusculas y valida el formato ABC-123. Recibe la placa."""
    placa = valor.strip().upper()
    if not PATRON_PLACA.match(placa):
        raise ValueError("La placa debe tener el formato ABC-123.")
    return placa


def _texto_limpio(valor: Optional[str]) -> Optional[str]:
    """Quita espacios sobrantes y convierte el texto vacio en None. Recibe el texto."""
    if valor is None:
        return None
    limpio = valor.strip()
    return limpio or None


# ---------------------------------------------------------------------------
# Documentos de la flota
# ---------------------------------------------------------------------------


class DocumentoBase(BaseModel):
    """Datos comunes de un documento de flota."""

    placa: str
    tipo_documento: TipoDocumentoEnum
    numero: str = Field(..., min_length=1, max_length=60)
    entidad_emisora: Optional[str] = Field(None, max_length=120)
    fecha_emision: date
    fecha_vencimiento: date
    archivo_url: Optional[str] = Field(None, max_length=300)
    observaciones: Optional[str] = Field(None, max_length=1000)

    @field_validator("placa")
    @classmethod
    def validar_placa(cls, valor: str) -> str:
        """Normaliza y valida la placa. Recibe la placa escrita por el usuario."""
        return _normalizar_placa(valor)

    @field_validator("numero", "entidad_emisora", "archivo_url", "observaciones")
    @classmethod
    def limpiar_textos(cls, valor: Optional[str]) -> Optional[str]:
        """Limpia espacios y deja None en los campos opcionales vacios."""
        return _texto_limpio(valor)

    @model_validator(mode="after")
    def validar_fechas(self):
        """Exige que el vencimiento sea posterior a la emision."""
        if self.fecha_vencimiento <= self.fecha_emision:
            raise ValueError("La fecha de vencimiento debe ser posterior a la fecha de emisión.")
        return self


class DocumentoCreateRequest(DocumentoBase):
    """Datos para registrar un documento de flota."""


class DocumentoUpdateRequest(BaseModel):
    """Cambios parciales de un documento. Todos los campos son opcionales."""

    placa: Optional[str] = None
    tipo_documento: Optional[TipoDocumentoEnum] = None
    numero: Optional[str] = Field(None, min_length=1, max_length=60)
    entidad_emisora: Optional[str] = Field(None, max_length=120)
    fecha_emision: Optional[date] = None
    fecha_vencimiento: Optional[date] = None
    archivo_url: Optional[str] = Field(None, max_length=300)
    observaciones: Optional[str] = Field(None, max_length=1000)

    @field_validator("placa")
    @classmethod
    def validar_placa(cls, valor: Optional[str]) -> Optional[str]:
        """Normaliza y valida la placa si viene en la peticion."""
        return _normalizar_placa(valor) if valor is not None else None

    @field_validator("numero", "entidad_emisora", "archivo_url", "observaciones")
    @classmethod
    def limpiar_textos(cls, valor: Optional[str]) -> Optional[str]:
        """Limpia espacios y deja None en los campos opcionales vacios."""
        return _texto_limpio(valor)


class DocumentoResponse(DocumentoBase):
    """Documento con su estado calculado y sus datos de auditoria."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: Optional[str] = None
    estado: EstadoDocumentoEnum
    dias_para_vencer: int
    creado_por: str
    creado_en: datetime
    actualizado_por: Optional[str] = None
    actualizado_en: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Mantenimientos
# ---------------------------------------------------------------------------


class MantenimientoCreateRequest(BaseModel):
    """Datos para programar o registrar un mantenimiento."""

    placa: str
    tipo: TipoMantenimientoEnum = TipoMantenimientoEnum.PREVENTIVO
    categoria: CategoriaMantenimientoEnum = CategoriaMantenimientoEnum.REVISION_GENERAL
    descripcion: str = Field(..., min_length=5, max_length=1000)
    prioridad: PrioridadMantenimientoEnum = PrioridadMantenimientoEnum.MEDIA
    estado: EstadoMantenimientoEnum = EstadoMantenimientoEnum.PROGRAMADO
    fecha_programada: date
    fecha_ejecucion: Optional[date] = None
    kilometraje: Optional[int] = Field(None, ge=0, le=5_000_000)
    costo: Optional[float] = Field(None, ge=0, le=10_000_000)
    taller: Optional[str] = Field(None, max_length=120)
    observaciones: Optional[str] = Field(None, max_length=1000)

    @field_validator("placa")
    @classmethod
    def validar_placa(cls, valor: str) -> str:
        """Normaliza y valida la placa. Recibe la placa escrita por el usuario."""
        return _normalizar_placa(valor)

    @field_validator("descripcion", "taller", "observaciones")
    @classmethod
    def limpiar_textos(cls, valor: Optional[str]) -> Optional[str]:
        """Limpia espacios y deja None en los campos opcionales vacios."""
        return _texto_limpio(valor)

    @model_validator(mode="after")
    def validar_completado(self):
        """Un mantenimiento COMPLETADO debe traer fecha de ejecucion."""
        if self.estado == EstadoMantenimientoEnum.COMPLETADO and self.fecha_ejecucion is None:
            raise ValueError("Un mantenimiento COMPLETADO debe indicar la fecha de ejecución.")
        return self


class MantenimientoUpdateRequest(BaseModel):
    """Cambios parciales de un mantenimiento. Todos los campos son opcionales."""

    placa: Optional[str] = None
    tipo: Optional[TipoMantenimientoEnum] = None
    categoria: Optional[CategoriaMantenimientoEnum] = None
    descripcion: Optional[str] = Field(None, min_length=5, max_length=1000)
    prioridad: Optional[PrioridadMantenimientoEnum] = None
    estado: Optional[EstadoMantenimientoEnum] = None
    fecha_programada: Optional[date] = None
    fecha_ejecucion: Optional[date] = None
    kilometraje: Optional[int] = Field(None, ge=0, le=5_000_000)
    costo: Optional[float] = Field(None, ge=0, le=10_000_000)
    taller: Optional[str] = Field(None, max_length=120)
    observaciones: Optional[str] = Field(None, max_length=1000)

    @field_validator("placa")
    @classmethod
    def validar_placa(cls, valor: Optional[str]) -> Optional[str]:
        """Normaliza y valida la placa si viene en la peticion."""
        return _normalizar_placa(valor) if valor is not None else None

    @field_validator("descripcion", "taller", "observaciones")
    @classmethod
    def limpiar_textos(cls, valor: Optional[str]) -> Optional[str]:
        """Limpia espacios y deja None en los campos opcionales vacios."""
        return _texto_limpio(valor)


class CompletarMantenimientoRequest(BaseModel):
    """Datos opcionales al cerrar un mantenimiento."""

    fecha_ejecucion: Optional[date] = None
    kilometraje: Optional[int] = Field(None, ge=0, le=5_000_000)
    costo: Optional[float] = Field(None, ge=0, le=10_000_000)
    taller: Optional[str] = Field(None, max_length=120)
    observaciones: Optional[str] = Field(None, max_length=1000)

    @field_validator("taller", "observaciones")
    @classmethod
    def limpiar_textos(cls, valor: Optional[str]) -> Optional[str]:
        """Limpia espacios y deja None en los campos opcionales vacios."""
        return _texto_limpio(valor)


class MantenimientoResponse(BaseModel):
    """Mantenimiento con su estado de vencimiento y datos de auditoria."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: Optional[str] = None
    placa: str
    tipo: TipoMantenimientoEnum
    categoria: CategoriaMantenimientoEnum
    descripcion: str
    prioridad: PrioridadMantenimientoEnum
    estado: EstadoMantenimientoEnum
    fecha_programada: Optional[date] = None
    fecha_ejecucion: Optional[date] = None
    kilometraje: Optional[int] = None
    costo: Optional[float] = None
    moneda: str
    taller: Optional[str] = None
    observaciones: Optional[str] = None
    vencido: bool
    dias_para_programado: Optional[int] = None
    creado_por: str
    creado_en: datetime
    actualizado_por: Optional[str] = None
    actualizado_en: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Semana 14: preventivos, averias, combustible y costos
# ---------------------------------------------------------------------------


class PreventivoCreateRequest(BaseModel):
    """Datos para crear un plan de mantenimiento preventivo."""

    placa: str
    categoria: CategoriaMantenimientoEnum
    descripcion: str = Field(..., min_length=5, max_length=1000)
    intervalo_km: int = Field(..., ge=1, le=500_000)
    intervalo_dias: Optional[int] = Field(None, ge=1, le=3650)
    km_base: Optional[int] = Field(None, ge=0, le=5_000_000)
    fecha_base: Optional[date] = None

    @field_validator("placa")
    @classmethod
    def validar_placa(cls, valor: str) -> str:
        """Normaliza y valida la placa. Recibe la placa escrita por el usuario."""
        return _normalizar_placa(valor)

    @field_validator("descripcion")
    @classmethod
    def limpiar_descripcion(cls, valor: str) -> str:
        """Quita los espacios sobrantes de la descripcion."""
        return valor.strip()

    @model_validator(mode="after")
    def validar_intervalos(self):
        """Exige al menos un criterio: kilometraje o dias (el km siempre va)."""
        if self.intervalo_km is None and self.intervalo_dias is None:
            raise ValueError("El plan debe indicar un intervalo en kilómetros o en días.")
        return self


class PreventivoUpdateRequest(BaseModel):
    """Cambios parciales de un plan preventivo. Todos los campos son opcionales."""

    placa: Optional[str] = None
    categoria: Optional[CategoriaMantenimientoEnum] = None
    descripcion: Optional[str] = Field(None, min_length=5, max_length=1000)
    intervalo_km: Optional[int] = Field(None, ge=1, le=500_000)
    intervalo_dias: Optional[int] = Field(None, ge=1, le=3650)
    km_base: Optional[int] = Field(None, ge=0, le=5_000_000)
    fecha_base: Optional[date] = None
    activo: Optional[bool] = None

    @field_validator("placa")
    @classmethod
    def validar_placa(cls, valor: Optional[str]) -> Optional[str]:
        """Normaliza y valida la placa si viene en la peticion."""
        return _normalizar_placa(valor) if valor is not None else None

    @field_validator("descripcion")
    @classmethod
    def limpiar_descripcion(cls, valor: Optional[str]) -> Optional[str]:
        """Limpia espacios y deja None en la descripcion vacia."""
        return _texto_limpio(valor)


class PreventivoResponse(BaseModel):
    """Plan preventivo con su estado calculado en lectura."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: Optional[str] = None
    placa: str
    categoria: CategoriaMantenimientoEnum
    descripcion: str
    intervalo_km: int
    intervalo_dias: Optional[int] = None
    km_base: Optional[int] = None
    km_actual: int
    km_restantes: int
    fecha_base: Optional[date] = None
    fecha_limite: Optional[date] = None
    dias_restantes: Optional[int] = None
    estado: EstadoPreventivoEnum
    activo: bool
    creado_por: str
    creado_en: datetime


class AveriaVehiculoResponse(BaseModel):
    """Ranking de unidades con mas incidencias de auxilio mecanico."""

    placa: str
    total: int
    abiertas: int
    resueltas: int
    ultima_fecha: Optional[date] = None
    sugerencia: str


class CargaCombustibleCreateRequest(BaseModel):
    """Datos para registrar una carga de combustible."""

    placa: str
    fecha: date
    tipo_combustible: TipoCombustibleEnum = TipoCombustibleEnum.DIESEL
    galones: float = Field(..., gt=0, le=1000)
    monto: float = Field(..., gt=0, le=1_000_000)
    odometro: Optional[int] = Field(None, ge=0, le=5_000_000)
    proveedor: Optional[str] = Field(None, max_length=120)
    observaciones: Optional[str] = Field(None, max_length=1000)

    @field_validator("placa")
    @classmethod
    def validar_placa(cls, valor: str) -> str:
        """Normaliza y valida la placa. Recibe la placa escrita por el usuario."""
        return _normalizar_placa(valor)

    @field_validator("proveedor", "observaciones")
    @classmethod
    def limpiar_textos(cls, valor: Optional[str]) -> Optional[str]:
        """Limpia espacios y deja None en los campos opcionales vacios."""
        return _texto_limpio(valor)


class CargaCombustibleUpdateRequest(BaseModel):
    """Cambios parciales de una carga. Todos los campos son opcionales."""

    placa: Optional[str] = None
    fecha: Optional[date] = None
    tipo_combustible: Optional[TipoCombustibleEnum] = None
    galones: Optional[float] = Field(None, gt=0, le=1000)
    monto: Optional[float] = Field(None, gt=0, le=1_000_000)
    odometro: Optional[int] = Field(None, ge=0, le=5_000_000)
    proveedor: Optional[str] = Field(None, max_length=120)
    observaciones: Optional[str] = Field(None, max_length=1000)

    @field_validator("placa")
    @classmethod
    def validar_placa(cls, valor: Optional[str]) -> Optional[str]:
        """Normaliza y valida la placa si viene en la peticion."""
        return _normalizar_placa(valor) if valor is not None else None

    @field_validator("proveedor", "observaciones")
    @classmethod
    def limpiar_textos(cls, valor: Optional[str]) -> Optional[str]:
        """Limpia espacios y deja None en los campos opcionales vacios."""
        return _texto_limpio(valor)


class CargaCombustibleResponse(BaseModel):
    """Carga con rendimiento calculado y marca de consumo anomalo."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: Optional[str] = None
    placa: str
    fecha: date
    tipo_combustible: TipoCombustibleEnum
    galones: float
    monto: float
    odometro: Optional[int] = None
    proveedor: Optional[str] = None
    observaciones: Optional[str] = None
    km_recorridos: Optional[float] = None
    rendimiento_km_gal: Optional[float] = None
    consumo_anomalo: bool = False
    creado_por: str
    creado_en: datetime


class CostosFlotaResponse(BaseModel):
    """Costos y rendimiento global de la flota (mantenimiento + combustible)."""

    costo_mantenimiento: float
    costo_combustible: float
    costo_total: float
    km_totales: float
    costo_por_kilometro: Optional[float] = None
    galones_totales: float
    rendimiento_km_gal: Optional[float] = None
    cargas_totales: int
    mantenimientos_completados: int
    preventivos_vencidos: int
    moneda: str


# ---------------------------------------------------------------------------
# Resumen, alertas, flota, configuracion y auditoria
# ---------------------------------------------------------------------------


class ResumenResponse(BaseModel):
    """Indicadores del modulo para el panel."""

    total_vehiculos: int
    documentos_total: int
    documentos_vigentes: int
    documentos_por_vencer: int
    documentos_vencidos: int
    documentos_por_tipo: Dict[str, int]
    mantenimientos_total: int
    mantenimientos_programados: int
    mantenimientos_en_proceso: int
    mantenimientos_completados: int
    mantenimientos_vencidos: int
    costo_mes: float
    costo_total: float  # mantenimiento; el combustible se reporta aparte
    costo_combustible: float = 0
    costo_por_kilometro: Optional[float] = None
    rendimiento_km_gal: Optional[float] = None
    preventivos_vencidos: int = 0
    consumos_anomalos: int = 0
    moneda: str
    alertas_total: int
    alertas_alta: int
    vehiculos_sin_documentos: int


class AlertaResponse(BaseModel):
    """Aviso calculado: documento, licencia o mantenimiento vencido o por vencer."""

    id: str
    tipo: str
    severidad: str
    placa: Optional[str] = None
    conductor: Optional[str] = None
    titulo: str
    mensaje: str
    fecha_referencia: Optional[date] = None
    dias: Optional[int] = None
    umbral: Optional[int] = None  # 30, 15 o 7 cuando aplica
    entidad_id: Optional[int] = None


class FlotaEstadoResponse(BaseModel):
    """Estado documental y de mantenimiento de un vehiculo."""

    placa: str
    marca: Optional[str] = None
    estado_vehiculo: Optional[str] = None
    documentos_total: int
    documentos_vencidos: int
    documentos_por_vencer: int
    documentos_faltantes: List[str]
    proximo_vencimiento: Optional[date] = None
    mantenimientos_abiertos: int
    proximo_mantenimiento: Optional[date] = None
    estado_general: str
    apto_para_salir: bool
    motivos_no_apto: List[str] = Field(default_factory=list)


class LicenciaResponse(BaseModel):
    """Licencia de conducir con su vencimiento calculado (solo administradores)."""

    conductor_id: int
    usuario_id: int
    nombre: str
    correo: Optional[str] = None
    dni: Optional[str] = None
    licencia_numero: Optional[str] = None
    licencia_vencimiento: Optional[date] = None
    estado: str
    dias_para_vencer: Optional[int] = None
    nivel_alerta: Optional[str] = None
    umbral: Optional[int] = None


class CostosVehiculoResponse(BaseModel):
    """Costos de mantenimiento y combustible acumulados de una unidad."""

    costo_total: float
    costo_mes: float
    costo_mantenimiento: float = 0
    costo_combustible: float = 0
    costo_por_kilometro: Optional[float] = None
    rendimiento_km_gal: Optional[float] = None
    moneda: str
    mantenimientos_completados: int
    cargas_totales: int = 0
    ultimo_kilometraje: Optional[int] = None


class FichaVehiculoResponse(BaseModel):
    """Ficha de estado de una unidad: documentos, mantenimientos y costos."""

    placa: str
    marca: Optional[str] = None
    codigo: Optional[str] = None
    estado_vehiculo: Optional[str] = None
    odometro_actual: Optional[int] = None
    documentos: List[DocumentoResponse]
    mantenimientos: List[MantenimientoResponse]
    preventivos: List[PreventivoResponse] = Field(default_factory=list)
    cargas: List[CargaCombustibleResponse] = Field(default_factory=list)
    averias: List[AveriaVehiculoResponse] = Field(default_factory=list)
    costos: CostosVehiculoResponse
    documentos_total: int
    documentos_vencidos: int
    documentos_por_vencer: int
    documentos_faltantes: List[str]
    proximo_vencimiento: Optional[date] = None
    mantenimientos_abiertos: int
    proximo_mantenimiento: Optional[date] = None
    estado_general: str
    apto_para_salir: bool
    motivos_no_apto: List[str] = Field(default_factory=list)


class ConfiguracionResponse(BaseModel):
    """Parametros vigentes del modulo."""

    model_config = ConfigDict(from_attributes=True)

    dias_aviso_documento: int
    dias_aviso_mantenimiento: int
    moneda: str
    alertas_documentos: bool
    alertas_mantenimientos: bool
    tolerancia_consumo: int = 20
    actualizado_por: Optional[str] = None
    actualizado_en: Optional[datetime] = None


class ConfiguracionUpdateRequest(BaseModel):
    """Cambios parciales de configuracion."""

    dias_aviso_documento: Optional[int] = Field(None, ge=1, le=365)
    dias_aviso_mantenimiento: Optional[int] = Field(None, ge=1, le=365)
    moneda: Optional[str] = Field(None, min_length=3, max_length=3)
    alertas_documentos: Optional[bool] = None
    alertas_mantenimientos: Optional[bool] = None
    tolerancia_consumo: Optional[int] = Field(None, ge=1, le=100)

    @field_validator("moneda")
    @classmethod
    def validar_moneda(cls, valor: Optional[str]) -> Optional[str]:
        """Exige un codigo de moneda de tres letras (PEN, USD...). Recibe el codigo."""
        if valor is None:
            return None
        moneda = valor.strip().upper()
        if not moneda.isalpha():
            raise ValueError("La moneda debe tener tres letras, por ejemplo PEN.")
        return moneda


class AuditoriaResponse(BaseModel):
    """Movimiento registrado en la auditoria del modulo."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    accion: str
    entidad: str
    entidad_id: Optional[str] = None
    detalle: Optional[str] = None
    usuario: str
    creado_en: datetime
