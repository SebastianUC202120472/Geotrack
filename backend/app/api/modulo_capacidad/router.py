import json
import os
from typing import List
from datetime import datetime
from fastapi import APIRouter, HTTPException, status
from pydantic import ValidationError

from .schemas import (
    ModeloVehiculo, 
    CatalogoEstructuraJSON, 
    VinculacionPlacaRequest, 
    VinculacionPlacaResponse
)

router = APIRouter(
    prefix="",
    tags=["Módulo Capacidad y Catálogo"]
)

JSON_PATH = os.path.join(os.path.dirname(__file__), "catalogo_vehiculos.json")

CATALOGO_MEMORIA: List[ModeloVehiculo] = []
VERSION_CATALOGO = "1.1.0"

def cargar_y_validar_catalogo_al_arrancar():
    global CATALOGO_MEMORIA, VERSION_CATALOGO
    if not os.path.exists(JSON_PATH):
        print(" Advertencia: No existe catalogo_vehiculos.json.")
        return

    try:
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            contenido_raw = json.load(f)
            
        estructura = CatalogoEstructuraJSON(**contenido_raw)
        
        ids_vistos = set()
        for mod in estructura.modelos:
            if mod.id in ids_vistos:
                raise ValueError(f"ID duplicado detectado: {mod.id}")
            ids_vistos.add(mod.id)

        CATALOGO_MEMORIA = estructura.modelos
        VERSION_CATALOGO = estructura.version
        print(f" Catálogo cargado en memoria exitosamente: {len(CATALOGO_MEMORIA)} modelos.")

    except ValidationError as e:
        print(f" ERROR DE VALIDACIÓN EN EL JSON:\n{e}")
        CATALOGO_MEMORIA = []
    except Exception as e:
        print(f" ERROR GENERAL: {e}")
        CATALOGO_MEMORIA = []

cargar_y_validar_catalogo_al_arrancar()

# --- ENDPOINTS DE CATÁLOGO ---

@router.get("/catalogo", response_model=List[ModeloVehiculo])
def obtener_catalogo():
    """Retorna la lista completa de modelos desde la memoria rápida."""
    return CATALOGO_MEMORIA

@router.get("/catalogo/{modelo_id}", response_model=ModeloVehiculo)
def obtener_modelo_por_id(modelo_id: str):
    """Busca un modelo en el catálogo por su ID."""
    modelo = next((m for m in CATALOGO_MEMORIA if m.id == modelo_id), None)
    if not modelo:
        raise HTTPException(status_code=404, detail="Modelo no encontrado en el catálogo")
    return modelo

# --- ENDPOINTS DE VINCULACIÓN ---

@router.post("/vincular", response_model=VinculacionPlacaResponse, status_code=status.HTTP_201_CREATED)
def vincular_placa(data: VinculacionPlacaRequest):
    """Vincular una placa peruana a un modelo existente del catálogo."""
    modelo_encontrado = next((m for m in CATALOGO_MEMORIA if m.id == data.modelo_id), None)
    if not modelo_encontrado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"El modelo con ID '{data.modelo_id}' no existe en el catálogo."
        )

    return VinculacionPlacaResponse(
        id=1,
        placa=data.placa.upper(),
        modelo=modelo_encontrado,
        creado_por="admin@geotrack.com",
        creado_en=datetime.now().isoformat()
    )