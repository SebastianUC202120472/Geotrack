from enum import Enum
from pydantic import BaseModel, Field, model_validator
from typing import Optional, List
import re

class TipoVehiculoEnum(str, Enum):
    PICKUP = "pickup"
    FURGONETA = "furgoneta"
    CAMION_LIGERO = "camion_ligero"
    CAMION_MEDIANO = "camion_mediano"
    CAMION_PESADO = "camion_pesado"

class ModeloVehiculo(BaseModel):
    id: str = Field(..., description="ID único del modelo")
    marca: str = Field(..., description="Marca oficial")
    modelo: str = Field(..., description="Modelo o línea")
    tipo: TipoVehiculoEnum = Field(..., description="Tipo restringido por Enum")
    largo_m: float = Field(..., gt=0, lt=20)
    ancho_m: float = Field(..., gt=0, lt=4)
    alto_m: float = Field(..., gt=0, lt=4)
    volumen_util_m3: float = Field(..., gt=0)
    carga_util_kg: float = Field(..., gt=0, lt=50000)  # Nombre alineado con el JSON
    fuente: Optional[str] = Field(None)
    fuente_url: Optional[str] = Field(None)
    verificado: Optional[bool] = Field(False)

    @model_validator(mode='after')
    def validar_coherencia_volumen_y_carga(self):
        volumen_calculado = self.largo_m * self.ancho_m * self.alto_m
        limite_inferior = volumen_calculado * 0.80
        limite_superior = volumen_calculado * 1.20
        
        if not (limite_inferior <= self.volumen_util_m3 <= limite_superior):
            raise ValueError(
                f"El volumen útil ({self.volumen_util_m3} m³) difiere más del 20% del volumen "
                f"teórico ({volumen_calculado:.2f} m³)."
            )
        return self

class CatalogoEstructuraJSON(BaseModel):
    version: str
    actualizado_en: str
    modelos: List[ModeloVehiculo]

class VinculacionPlacaRequest(BaseModel):
    placa: str
    modelo_id: str

    @model_validator(mode='after')
    def validar_formato_placa_peru(self):
        patron_peru = r'^[A-Z0-9]{3}-[A-Z0-9]{3}$'
        if not re.match(patron_peru, self.placa.upper()):
            raise ValueError("La placa debe cumplir con el formato peruano (ej. ABC-123).")
        self.placa = self.placa.upper()
        return self

class VinculacionPlacaResponse(BaseModel):
    id: int
    placa: str
    modelo: ModeloVehiculo
    creado_por: str
    creado_en: str

class TamanioEstandarEnum(str, Enum):
    S = "S"  # 0.05 m3 / 5 kg
    M = "M"  # 0.25 m3 / 20 kg
    L = "L"  # 1.00 m3 / 150 kg

class PaqueteRequest(BaseModel):
    tamanio: TamanioEstandarEnum
    cantidad: int = Field(..., gt=0, description="Cantidad de bultos/paquetes")

class CalculadoraCapacidadRequest(BaseModel):
    vehiculo_id: str
    capacidad_max_m3: float = Field(..., gt=0)
    capacidad_max_kg: float = Field(..., gt=0)
    paquetes: List[PaqueteRequest]

