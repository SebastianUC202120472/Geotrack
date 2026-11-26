import hashlib
import io
from typing import Optional, Tuple
import numpy as np
from PIL import Image, ImageOps
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.registro import obtener_logger
from app.models.analisis import EvidenciaAnalisis

_log = obtener_logger("hash_perceptual")


def calcular_sha256(datos: bytes) -> str:
    """Calcula el hash criptográfico SHA-256 de los bytes del archivo."""
    return hashlib.sha256(datos).hexdigest()


def _calcular_dhash_nativo(img: Image.Image) -> str:
    """Calcula la huella perceptual dHash (Difference Hash) de 64 bits usando NumPy.
    Resistente a cambios de resolución, compresión JPEG y variaciones menores de brillo.
    """
    # 1. Reducir a 9x8 en escala de grises (9 columnas para calcular 8 diferencias por fila)
    reducida = img.convert("L").resize((9, 8), Image.Resampling.LANCZOS)
    arr = np.asarray(reducida, dtype=np.int16)

    # 2. Comparar píxeles adyacentes horizontalmente (8x8 booleanos = 64 bits)
    diferencias = arr[:, 1:] > arr[:, :-1]

    # 3. Empaquetar los 64 bits en un entero y formatear a 16 caracteres hexadecimales
    bits = diferencias.flatten()
    valor_entero = 0
    for bit in bits:
        valor_entero = (valor_entero << 1) | int(bit)

    return f"{valor_entero:016x}"


def calcular_perceptual_hash(datos: bytes) -> str:
    """Genera la huella perceptual de la imagen. Usa la librería imagehash si está instalada,
    o el motor nativo de dHash optimizado en NumPy como fallback garantizado.
    """
    buffer = io.BytesIO(datos)
    with Image.open(buffer) as img_raw:
        img = ImageOps.exif_transpose(img_raw) or img_raw
        try:
            import imagehash
            return str(imagehash.dhash(img))
        except ImportError:
            return _calcular_dhash_nativo(img)


def distancia_hamming(hash1: str, hash2: str) -> int:
    """Calcula la distancia de Hamming (número de bits diferentes) entre dos huellas hexadecimales."""
    if not hash1 or not hash2:
        return 64
    try:
        val1 = int(hash1, 16)
        val2 = int(hash2, 16)
        return bin(val1 ^ val2).count("1")
    except ValueError:
        return 64


def buscar_foto_reciclada(
    db: Session,
    hash_perceptual: str,
    sha256_actual: str,
    evidencia_id_actual: int,
) -> Tuple[bool, Optional[int], Optional[int]]:
    """Compara la huella perceptual y SHA-256 contra evidencias previas en la base de datos.
    Devuelve: (es_duplicada, evidencia_id_coincidente, distancia_minima_hamming)
    """
    if not hash_perceptual:
        return False, None, None

    # 1. Detección rápida de archivo exactamente idéntico por SHA-256
    coincidencia_exacta = db.query(EvidenciaAnalisis).filter(
        EvidenciaAnalisis.sha256 == sha256_actual,
        EvidenciaAnalisis.evidencia_id != evidencia_id_actual,
    ).first()

    if coincidencia_exacta:
        _log.warning(
            "Foto idéntica (SHA-256 exacto) detectada: evidencia %d coincide con evidencia %d.",
            evidencia_id_actual,
            coincidencia_exacta.evidencia_id,
        )
        return True, coincidencia_exacta.evidencia_id, 0

    # 2. Detección perceptual de imagen reciclada (re-comprimida o con edición leve)
    # Consultamos las últimas evidencias analizadas (hasta 1000 previas para no saturar memoria)
    evidencias_previas = db.query(
        EvidenciaAnalisis.evidencia_id,
        EvidenciaAnalisis.perceptual_hash,
    ).filter(
        EvidenciaAnalisis.evidencia_id != evidencia_id_actual,
        EvidenciaAnalisis.perceptual_hash.isnot(None),
    ).order_by(EvidenciaAnalisis.id.desc()).limit(1000).all()

    min_distancia = 64
    coincidencia_id = None

    for ev_id, p_hash in evidencias_previas:
        dist = distancia_hamming(hash_perceptual, p_hash)
        if dist < min_distancia:
            min_distancia = dist
            coincidencia_id = ev_id

        if dist <= settings.HAMMING_DISTANCE_DUPLICATE:
            _log.warning(
                "Foto reciclada detectada por huella perceptual: evidencia %d vs %d (distancia Hamming: %d <= %d).",
                evidencia_id_actual,
                ev_id,
                dist,
                settings.HAMMING_DISTANCE_DUPLICATE,
            )
            return True, ev_id, dist

    return False, None, min_distancia if min_distancia < 64 else None
