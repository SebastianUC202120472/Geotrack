import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from typing import List
from app.api.modulo_capacidad.schemas import ModeloVehiculo

router = APIRouter()

CATALOGO_PATH = Path(__file__).resolve().parent / "catalogo_vehiculos.json"

@router.get("/catalogo", response_model=List[ModeloVehiculo])
def cargar_catalogo() -> List[ModeloVehiculo]:
    if not CATALOGO_PATH.exists():
        raise HTTPException(status_code=404, detail="Archivo catalogo_vehiculos.json no encontrado")
    with open(CATALOGO_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [ModeloVehiculo(**item) for item in data]

@router.get("/catalogo", response_model=List[ModeloVehiculo])
def obtener_catalogo():
    """Retorna la lista completa de modelos de vehículos del catálogo JSON."""
    return cargar_catalogo()

@router.get("/catalogo/{modelo_id}", response_model=ModeloVehiculo)
def obtener_modelo(modelo_id: str):
    """Busca y retorna un modelo específico por su ID."""
    catalogo = cargar_catalogo()
    for item in catalogo:
        if item.id == modelo_id:
            return item
    raise HTTPException(status_code=404, detail="Modelo no encontrado")