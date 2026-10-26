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
    VinculacionPlacaResponse,
    CalculadoraCapacidadRequest
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

# --- ENDPOINTS: CALCULADORA DE CAPACIDAD Y ALERTAS ---

MEDIDAS_ESTANDAR = {
    "S": {"m3": 0.05, "kg": 5.0},
    "M": {"m3": 0.25, "kg": 20.0},
    "L": {"m3": 1.00, "kg": 150.0}
}

@router.post("/calcular-capacidad")
def calcular_capacidad(req: CalculadoraCapacidadRequest):
    volumen_total = 0.0
    peso_total = 0.0

    for item in req.paquetes:
        medida = MEDIDAS_ESTANDAR[item.tamanio.value]
        volumen_total += medida["m3"] * item.cantidad
        peso_total += medida["kg"] * item.cantidad

    pct_m3 = round((volumen_total / req.capacidad_max_m3) * 100, 2)
    pct_kg = round((peso_total / req.capacidad_max_kg) * 100, 2)
    
    excede = pct_m3 > 100.0 or pct_kg > 100.0

    if excede:
        nivel = "CRITICO"
        msg = f"¡ALERTA CRÍTICA! Se sobrepasa la capacidad ({pct_m3}% vol / {pct_kg}% peso)."
    elif pct_m3 >= 85.0 or pct_kg >= 85.0:
        nivel = "ADVERTENCIA"
        msg = f"Capacidad cercana al límite ({pct_m3}% vol / {pct_kg}% peso)."
    else:
        nivel = "OK"
        msg = f"Carga óptima dentro de los límites ({pct_m3}% vol / {pct_kg}% peso)."

    return {
        "volumen_total_m3": round(volumen_total, 2),
        "peso_total_kg": round(peso_total, 2),
        "excede_limite": excede,
        "alerta": {
            "nivel": nivel,
            "mensaje": msg,
            "porcentaje_m3": pct_m3,
            "porcentaje_kg": pct_kg
        }
    }