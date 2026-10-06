import io
import warnings

from fastapi import HTTPException, UploadFile, status
from PIL import Image

from app.core.config import settings

# Formato real (segun Pillow) -> extension con la que se guarda el archivo.
FORMATOS_IMAGEN = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}
_FORMATOS_TEXTO = "JPG, PNG o WEBP"
_BLOQUE = 64 * 1024


def _max_bytes() -> int:
    return settings.IMAGEN_MAX_MB * 1024 * 1024


async def leer_imagen_subida(file: UploadFile) -> bytes:
    """Lee el archivo subido por bloques y corta con 413 si supera IMAGEN_MAX_MB. Recibe el UploadFile."""
    limite = _max_bytes()
    # Corte temprano si el cliente declara el tamaño; igual se cuenta al leer
    # porque ese dato lo controla quien sube el archivo.
    if file.size is not None and file.size > limite:
        raise _muy_grande()
    bloques, total = [], 0
    while bloque := await file.read(_BLOQUE):
        total += len(bloque)
        if total > limite:
            raise _muy_grande()
        bloques.append(bloque)
    return b"".join(bloques)


def validar_imagen(contenido: bytes) -> str:
    """Verifica tamaño y tipo real de la imagen (por su contenido, no por el nombre). Recibe los bytes; devuelve la extension real."""
    if not contenido:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El archivo está vacío")
    if len(contenido) > _max_bytes():
        raise _muy_grande()

    try:
        with warnings.catch_warnings():
            # Una imagen con demasiados pixeles (bomba de descompresion) se rechaza, no se avisa.
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(contenido)) as imagen:
                formato = imagen.format
                imagen.verify()
    except Exception:
        raise _no_es_imagen()

    extension = FORMATOS_IMAGEN.get(formato)
    if not extension:
        raise _no_es_imagen()
    return extension


def _muy_grande() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        detail=f"La imagen supera el tamaño máximo de {settings.IMAGEN_MAX_MB} MB",
    )


def _no_es_imagen() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"El archivo no es una imagen válida. Usa: {_FORMATOS_TEXTO}",
    )
