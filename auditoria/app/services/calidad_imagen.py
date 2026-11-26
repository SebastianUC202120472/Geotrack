import io
from dataclasses import dataclass
from typing import Optional
import numpy as np
from PIL import Image, ImageOps

from app.core.config import settings
from app.core.registro import obtener_logger

_log = obtener_logger("calidad_imagen")


@dataclass
class ResultadoCalidadImagen:
    calidad_score: float             # 0.0 a 1.0
    es_borrosa: bool
    varianza_laplaciana: float
    es_oscura: bool
    es_sobreexpuesta: bool
    brillo_promedio: float
    resolucion_ancho: int
    resolucion_alto: int
    resolucion_baja: bool
    advertencias: list[str]


def calcular_varianza_laplaciana(arr_gris: np.ndarray) -> float:
    """Calcula la varianza del operador Laplaciano con NumPy puro (sin requerir OpenCV).
    Mide la cantidad de bordes de alta frecuencia: valores bajos indican desenfoque/borrosidad.
    """
    if arr_gris.shape[0] < 3 or arr_gris.shape[1] < 3:
        return 0.0

    # Kernel Laplaciano estándar 3x3:
    # [ 0,  1,  0]
    # [ 1, -4,  1]
    # [ 0,  1,  0]
    laplaciano = (
        arr_gris[:-2, 1:-1]
        + arr_gris[2:, 1:-1]
        + arr_gris[1:-1, :-2]
        + arr_gris[1:-1, 2:]
        - 4.0 * arr_gris[1:-1, 1:-1]
    )
    return float(laplaciano.var())


def evaluar_calidad_imagen(datos: bytes) -> ResultadoCalidadImagen:
    """Evalúa borrosidad, luminosidad y resolución de una imagen."""
    buffer = io.BytesIO(datos)
    with Image.open(buffer) as img_raw:
        # Corregir orientación según metadatos EXIF si existen
        img = ImageOps.exif_transpose(img_raw) or img_raw
        ancho, alto = img.size

        # Convertir a escala de grises para análisis de bordes y brillo
        img_gris = img.convert("L")
        arr = np.asarray(img_gris, dtype=np.float64)

    # 1. Medición de borrosidad
    var_lap = calcular_varianza_laplaciana(arr)
    es_borrosa = var_lap < settings.BLUR_THRESHOLD

    # 2. Medición de luminosidad / exposición
    brillo = float(arr.mean()) if arr.size > 0 else 0.0
    es_oscura = brillo < settings.DARK_THRESHOLD
    es_sobreexpuesta = brillo > settings.OVEREXPOSED_THRESHOLD

    # 3. Medición de resolución
    resolucion_baja = (ancho < settings.MIN_WIDTH) or (alto < settings.MIN_HEIGHT)

    # 4. Cálculo del score ponderado (0.0 a 1.0) y lista de advertencias
    score = 1.0
    advertencias = []

    if es_borrosa:
        score -= 0.4
        advertencias.append(f"Imagen borrosa/desenfocada (nitidez {var_lap:.1f} < {settings.BLUR_THRESHOLD})")

    if es_oscura:
        score -= 0.35
        advertencias.append(f"Imagen muy oscura/subexpuesta (brillo {brillo:.1f} < {settings.DARK_THRESHOLD})")
    elif es_sobreexpuesta:
        score -= 0.35
        advertencias.append(f"Imagen quemada/sobreexpuesta (brillo {brillo:.1f} > {settings.OVEREXPOSED_THRESHOLD})")

    if resolucion_baja:
        score -= 0.3
        advertencias.append(f"Resolución insuficiente ({ancho}x{alto} < {settings.MIN_WIDTH}x{settings.MIN_HEIGHT})")

    score_final = max(0.0, min(1.0, score))

    return ResultadoCalidadImagen(
        calidad_score=round(score_final, 2),
        es_borrosa=es_borrosa,
        varianza_laplaciana=round(var_lap, 2),
        es_oscura=es_oscura,
        es_sobreexpuesta=es_sobreexpuesta,
        brillo_promedio=round(brillo, 2),
        resolucion_ancho=ancho,
        resolucion_alto=alto,
        resolucion_baja=resolucion_baja,
        advertencias=advertencias,
    )
