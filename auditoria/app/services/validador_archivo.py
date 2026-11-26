import io
from dataclasses import dataclass
from typing import Optional
from PIL import Image

from app.core.config import settings
from app.core.registro import obtener_logger

_log = obtener_logger("validador_archivo")

# Fijar límite estricto de píxeles en Pillow para evitar Denegación de Servicio (DoS por Decompression Bomb)
Image.MAX_IMAGE_PIXELS = settings.MAX_PIXELS


@dataclass
class ResultadoValidacionArchivo:
    valido: bool
    formato: Optional[str] = None
    tamano_bytes: int = 0
    ancho: int = 0
    alto: int = 0
    es_bomba_descompresion: bool = False
    error: Optional[str] = None


def detectar_formato_magic_bytes(datos: bytes) -> Optional[str]:
    """Detecta el tipo de archivo real por sus primeros bytes de cabecera (magic bytes)."""
    if not datos or len(datos) < 12:
        return None

    if datos.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if datos.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if datos.startswith(b"RIFF") and datos[8:12] == b"WEBP":
        return "webp"

    return None


def validar_archivo_seguro(datos: bytes) -> ResultadoValidacionArchivo:
    """Valida tamaño, magic bytes y previene bombas de descompresión."""
    if not datos:
        return ResultadoValidacionArchivo(valido=False, error="Archivo vacío o sin contenido")

    tamano = len(datos)
    limite_max_bytes = settings.MAX_IMAGE_MB * 1024 * 1024

    if tamano > limite_max_bytes:
        return ResultadoValidacionArchivo(
            valido=False,
            tamano_bytes=tamano,
            error=f"Tamaño excede el máximo permitido ({tamano / (1024*1024):.2f} MB > {settings.MAX_IMAGE_MB} MB)",
        )

    formato = detectar_formato_magic_bytes(datos)
    if not formato:
        return ResultadoValidacionArchivo(
            valido=False,
            tamano_bytes=tamano,
            error="Formato no reconocido o no seguro (solo se aceptan JPEG, PNG, WEBP verificados por magic bytes)",
        )

    # Verificación de integridad y dimensiones con Pillow
    Image.MAX_IMAGE_PIXELS = settings.MAX_PIXELS
    try:
        buffer = io.BytesIO(datos)
        with Image.open(buffer) as img:
            ancho, alto = img.size
            total_pixeles = ancho * alto

            if total_pixeles > settings.MAX_PIXELS:
                return ResultadoValidacionArchivo(
                    valido=False,
                    formato=formato,
                    tamano_bytes=tamano,
                    ancho=ancho,
                    alto=alto,
                    es_bomba_descompresion=True,
                    error=f"Peligro: Bomba de descompresión detectada ({total_pixeles} píxeles > {settings.MAX_PIXELS})",
                )

            # Verificar integridad estructural del contenedor de imagen
            img.verify()

        return ResultadoValidacionArchivo(
            valido=True,
            formato=formato,
            tamano_bytes=tamano,
            ancho=ancho,
            alto=alto,
        )

    except Image.DecompressionBombError as e:
        _log.warning("DecompressionBombError detectado: %s", e)
        return ResultadoValidacionArchivo(
            valido=False,
            formato=formato,
            tamano_bytes=tamano,
            es_bomba_descompresion=True,
            error="Bomba de descompresión rechazada por protección activa de memoria",
        )
    except Exception as e:
        _log.warning("Archivo de imagen corrupto o inválido: %s", e)
        return ResultadoValidacionArchivo(
            valido=False,
            formato=formato,
            tamano_bytes=tamano,
            error=f"Imagen corrupta o con formato inválido: {str(e)}",
        )
