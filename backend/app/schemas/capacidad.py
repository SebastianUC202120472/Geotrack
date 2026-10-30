
# Esquemas Pydantic del modulo de catalogo y capacidad (Idea 3).
from datetime import date, datetime
from enum import Enum
from typing import Dict, List, Optional
from urllib.parse import urlparse
import ipaddress
import re

from pydantic import BaseModel, Field, StrictInt, model_validator


class TipoVehiculoEnum(str, Enum):
    PICKUP = "pickup"
    FURGONETA = "furgoneta"
    VAN = "van"
    SUV = "suv"
    SEDAN = "sedan"
    HATCHBACK = "hatchback"
    CAMION_LIGERO = "camion_ligero"
    CAMION_MEDIANO = "camion_mediano"
    CAMION_PESADO = "camion_pesado"


PATRON_PLACA = re.compile(r"^[A-Z0-9]{3}-[A-Z0-9]{3}$")
PATRON_ID = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"


def _validar_coherencia_volumen(
    largo_m: float, ancho_m: float, alto_m: float, volumen_util_m3: float
) -> None:
    """Comprueba que el volumen util no se aleje mas del 20% de las dimensiones.

    Recibe las tres dimensiones y el volumen declarado. Lanza ValueError si no cuadra.
    """
    volumen_teorico = largo_m * ancho_m * alto_m
    if not (volumen_teorico * 0.80 <= volumen_util_m3 <= volumen_teorico * 1.20):
        raise ValueError(
            f"El volumen util ({volumen_util_m3} m3) difiere mas del 20% del volumen "
            f"teorico ({volumen_teorico:.2f} m3)."
        )


class ModeloVehiculo(BaseModel):
    """Ficha tecnica de un modelo del catalogo."""

    id: str = Field(..., min_length=3, max_length=80, pattern=PATRON_ID)
    marca: str = Field(..., min_length=1, max_length=60)
    modelo: str = Field(..., min_length=1, max_length=80)
    tipo: TipoVehiculoEnum
    largo_m: float = Field(..., gt=0, lt=20)
    ancho_m: float = Field(..., gt=0, lt=4)
    alto_m: float = Field(..., gt=0, lt=4)
    volumen_util_m3: float = Field(..., gt=0, lt=200)
    carga_util_kg: float = Field(..., gt=0, lt=50000)
    fuente: Optional[str] = Field(None, max_length=200)
    fuente_url: Optional[str] = Field(None, max_length=300)
    verificado: bool = False
    es_personalizado: bool = False

    @model_validator(mode="after")
    def validar_coherencia(self):
        """Valida dimensiones contra volumen y devuelve el modelo."""
        _validar_coherencia_volumen(
            self.largo_m, self.ancho_m, self.alto_m, self.volumen_util_m3
        )
        return self


class CatalogoEstructuraJSON(BaseModel):
    version: str
    actualizado_en: str
    modelos: List[ModeloVehiculo]


def validar_fuente_tecnica(fuente: Optional[str], url_fuente: Optional[str]) -> None:
    """Exige referencia HTTPS, sin tratarla como verificacion documental."""
    if not fuente or not fuente.strip():
        raise ValueError("Indica la fuente de la ficha tecnica.")
    if not url_fuente or not url_fuente.strip():
        raise ValueError("Indica la URL de la ficha tecnica.")

    url = urlparse(url_fuente.strip())

    if url.scheme != "https" or not url.hostname or url.username or url.password:
        raise ValueError("La fuente debe ser una URL HTTPS publica valida.")

    if url.hostname.lower() == "localhost" or url.hostname.endswith(".local"):
        raise ValueError("No se aceptan direcciones locales como fuente.")

    try:
        if not ipaddress.ip_address(url.hostname).is_global:
            raise ValueError("No se aceptan direcciones IP privadas o reservadas.")
    except ValueError as exc:
        if "no se aceptan" in str(exc).lower():
            raise
        # Un nombre DNS normal no se puede interpretar como direccion IP.


class ModeloCreateRequest(BaseModel):
    """Alta de un modelo. El id se genera desde marca/modelo si no se envia."""

    id: Optional[str] = Field(None, min_length=3, max_length=80, pattern=PATRON_ID)
    marca: str = Field(..., min_length=1, max_length=60)
    modelo: str = Field(..., min_length=1, max_length=80)
    tipo: TipoVehiculoEnum
    largo_m: float = Field(..., gt=0, lt=20)
    ancho_m: float = Field(..., gt=0, lt=4)
    alto_m: float = Field(..., gt=0, lt=4)
    volumen_util_m3: float = Field(..., gt=0, lt=200)
    carga_util_kg: float = Field(..., gt=0, lt=50000)
    fuente: Optional[str] = Field(None, max_length=200)
    fuente_url: Optional[str] = Field(None, max_length=300)
    verificado: bool = False

    @model_validator(mode="after")
    def validar_coherencia(self):
        """Valida dimensiones contra volumen y devuelve el modelo."""
        _validar_coherencia_volumen(
            self.largo_m, self.ancho_m, self.alto_m, self.volumen_util_m3
        )
        validar_fuente_tecnica(self.fuente, self.fuente_url)
        return self


class ModeloUpdateRequest(BaseModel):
    """Edicion parcial de un modelo del catalogo."""

    marca: Optional[str] = Field(None, min_length=1, max_length=60)
    modelo: Optional[str] = Field(None, min_length=1, max_length=80)
    tipo: Optional[TipoVehiculoEnum] = None
    largo_m: Optional[float] = Field(None, gt=0, lt=20)
    ancho_m: Optional[float] = Field(None, gt=0, lt=4)
    alto_m: Optional[float] = Field(None, gt=0, lt=4)
    volumen_util_m3: Optional[float] = Field(None, gt=0, lt=200)
    carga_util_kg: Optional[float] = Field(None, gt=0, lt=50000)
    fuente: Optional[str] = Field(None, max_length=200)
    fuente_url: Optional[str] = Field(None, max_length=300)
    verificado: Optional[bool] = None

    @model_validator(mode="after")
    def exigir_al_menos_un_cambio(self):
        """Rechaza una peticion vacia. Devuelve el modelo."""
        if not self.model_dump(exclude_unset=True):
            raise ValueError("Indica al menos un campo a modificar.")
        return self


class VinculacionPlacaRequest(BaseModel):
    """Peticion para vincular una placa de la flota con un modelo."""

    placa: str
    modelo_id: str = Field(..., min_length=3, max_length=80)

    @model_validator(mode="after")
    def validar_formato_placa_peru(self):
        """Normaliza y valida el formato peruano ABC-123. Devuelve la peticion."""
        self.placa = self.placa.strip().upper()

        if not PATRON_PLACA.match(self.placa):
            raise ValueError("La placa debe tener el formato peruano (ej. ABC-123).")

        return self


class VinculacionResponse(BaseModel):
    id: int
    placa: str
    modelo_id: str
    modelo: Optional[ModeloVehiculo] = None
    marca: Optional[str] = None
    nombre_modelo: Optional[str] = None
    tipo: Optional[str] = None
    capacidad_m3: Optional[float] = None
    carga_kg: Optional[float] = None
    creado_por: str
    creado_en: datetime
    vehiculo_encontrado: bool = True
    conductor: Optional[str] = None


class FlotaVehiculoResponse(BaseModel):
    id: int
    placa: str
    marca: Optional[str] = None
    capacidad_volumetrica: Optional[float] = None
    capacidad_cajas: Optional[int] = None
    estado: Optional[str] = None
    conductor: Optional[str] = None
    vinculacion: Optional[VinculacionResponse] = None


class ConfiguracionResponse(BaseModel):
    factor_aprovechamiento: float
    max_paradas_por_viaje: int
    max_paradas_por_jornada: int
    max_viajes_por_dia: int

    s_peso_kg: float = 5.0
    s_volumen_m3: float = 0.03

    m_peso_kg: float = 15.0
    m_volumen_m3: float = 0.09

    l_peso_kg: float = 40.0
    l_volumen_m3: float = 0.25

    actualizado_por: Optional[str] = None
    actualizado_en: Optional[datetime] = None


class ConfiguracionUpdateRequest(BaseModel):
    factor_aprovechamiento: Optional[float] = Field(
        None, ge=0.5, le=1.0
    )

    max_paradas_por_viaje: Optional[int] = Field(
        None, ge=1, le=100
    )

    max_paradas_por_jornada: Optional[int] = Field(
        None, ge=1, le=500
    )

    max_viajes_por_dia: Optional[int] = Field(
        None, ge=1, le=20
    )

    s_peso_kg: Optional[float] = Field(None, gt=0, le=1000)
    s_volumen_m3: Optional[float] = Field(None, gt=0, le=100)

    m_peso_kg: Optional[float] = Field(None, gt=0, le=1000)
    m_volumen_m3: Optional[float] = Field(None, gt=0, le=100)

    l_peso_kg: Optional[float] = Field(None, gt=0, le=1000)
    l_volumen_m3: Optional[float] = Field(None, gt=0, le=100)

    @model_validator(mode="after")
    def validar_parametros(self):
        """Rechaza actualizaciones sin campos."""
        if not self.model_dump(exclude_unset=True):
            raise ValueError("Indica al menos un parametro a modificar.")
        return self


class FiltrosPedidos(BaseModel):
    """Filtros para tomar pedidos reales de la base."""

    estado: Optional[str] = Field(None, max_length=40)
    distrito: Optional[str] = Field(None, max_length=100)
    fecha: Optional[date] = None
    limite: Optional[int] = Field(None, ge=1, le=5000)


class CalculoRequest(BaseModel):
    """Calculadora: exactamente un origen de pedidos por solicitud."""

    modelo_id: Optional[str] = Field(None, min_length=3, max_length=80)
    placa: Optional[str] = Field(None, max_length=10)

    cantidades: Optional[Dict[str, StrictInt]] = None
    pedido_ids: Optional[List[int]] = Field(None, max_length=5000)
    filtros: Optional[FiltrosPedidos] = None
    demo_pedidos: Optional[int] = Field(None, ge=1, le=5000)

    factor_aprovechamiento: Optional[float] = Field(
        None, ge=0.5, le=1.0
    )

    max_paradas_por_viaje: Optional[int] = Field(
        None, ge=1, le=100
    )

    max_viajes_por_dia: Optional[int] = Field(
        None, ge=1, le=20
    )

    @model_validator(mode="after")
    def validar_origen(self):
        """Verifica el modelo seleccionado y el origen de los pedidos."""
        if not self.modelo_id and not self.placa:
            raise ValueError("Indica modelo_id o placa del vehiculo.")

        origenes = (
            self.cantidades is not None,
            self.pedido_ids is not None,
            self.filtros is not None,
            self.demo_pedidos is not None,
        )

        if sum(origenes) != 1:
            raise ValueError(
                "Indica exactamente un origen: cantidades, "
                "pedido_ids, filtros o demo_pedidos."
            )

        if self.pedido_ids is not None:
            if not self.pedido_ids or len(set(self.pedido_ids)) != len(self.pedido_ids):
                raise ValueError(
                    "Los pedido_ids no pueden ser vacios ni repetidos."
                )

            if any(i <= 0 for i in self.pedido_ids):
                raise ValueError(
                    "Los identificadores deben ser positivos."
                )

        if self.cantidades is not None:
            normalizadas: Dict[str, int] = {}

            for clave, valor in self.cantidades.items():
                tamano = str(clave).upper().strip()

                if tamano not in ("S", "M", "L"):
                    raise ValueError(
                        "Solo se aceptan tamanos S, M o L."
                    )

                if (
                    isinstance(valor, bool)
                    or not isinstance(valor, int)
                    or valor < 0
                ):
                    raise ValueError(
                        "Las cantidades deben ser enteros no negativos."
                    )

                normalizadas[tamano] = (
                    normalizadas.get(tamano, 0) + valor
                )

            if not 1 <= sum(normalizadas.values()) <= 5000:
                raise ValueError(
                    "El total debe tener entre 1 y 5000 cajas."
                )

            self.cantidades = normalizadas

        return self


class PedidoEnViaje(BaseModel):
    pedido_id: Optional[int] = None
    codigo: Optional[str] = None
    distrito: Optional[str] = None
    peso_kg: float
    volumen_m3: float
    estimado: bool = False
    tamano_estimado: Optional[str] = None


class ViajePlan(BaseModel):
    numero: int
    vehiculo_placa: str
    modelo_id: str
    marca: Optional[str] = None
    modelo: Optional[str] = None
    pedidos: List[PedidoEnViaje]
    paradas: int
    peso_kg: float
    volumen_m3: float
    utilizacion_pct: float
    utilizacion_peso_pct: float
    capacidad_m3: float
    capacidad_kg: float


class AlertaPlan(BaseModel):
    nivel: str  # info | warning | danger
    codigo: str
    mensaje: str


class ResumenPlan(BaseModel):
    total_pedidos: int
    pedidos_estimados: int
    peso_total_kg: float
    volumen_total_m3: float
    viajes_necesarios: int
    vehiculos_disponibles: int
    vehiculos_necesarios: Optional[int] = None
    vehiculos_usados: int = 0
    vehiculos_adicionales_estimados: Optional[int] = None
    utilizacion_promedio_pct: float
    paradas_maximas_por_viaje: int
    pedidos_sin_asignar: int


class VehiculoPlan(BaseModel):
    placa: str
    modelo_id: str
    marca: Optional[str] = None
    modelo: Optional[str] = None
    viajes: int
    pedidos: int
    peso_kg: float
    volumen_m3: float
    utilizacion_pct: float
    paradas: int


class PlanCapacidadResponse(BaseModel):
    modo: str
    configuracion: ConfiguracionResponse
    resumen: ResumenPlan
    vehiculos: List[VehiculoPlan]
    viajes: List[ViajePlan]
    alertas: List[AlertaPlan]


class AuditoriaResponse(BaseModel):
    id: int
    accion: str
    entidad: str
    entidad_id: Optional[str] = None
    detalle: Optional[str] = None
    usuario: str
    creado_en: datetime
