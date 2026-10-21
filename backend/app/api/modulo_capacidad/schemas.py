from pydantic import BaseModel, Field
from typing import Optional, List

class ModeloVehiculo(BaseModel):
    id: str
    marca: str
    modelo: str
    tipo: str  # sedan, hatchback, suv, pickup, furgoneta, van, camion_ligero
    largo_m: float = Field(..., gt=0, description="Largo de carga en metros")
    ancho_m: float = Field(..., gt=0, description="Ancho de carga en metros")
    alto_m: float = Field(..., gt=0, description="Alto de carga en metros")
    volumen_util_m3: float = Field(..., gt=0, description="Volumen útil de carga")
    carga_util_kg: float = Field(..., gt=0, description="Carga útil máxima")
    fuente: str = Field(..., description="Ficha técnica oficial o catálogo")

class VinculacionVehiculoModelo(BaseModel):
    placa: str
    modelo_id: str