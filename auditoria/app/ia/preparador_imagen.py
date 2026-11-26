import base64
import io
from typing import Tuple
from PIL import Image, ImageOps

from app.core.config import settings


def preparar_imagen_para_ia(
    datos: bytes,
    max_lado: int | None = None,
    calidad_jpeg: int = 80,
) -> Tuple[bytes, str]:
    """Prepara y sanitiza una imagen antes de enviarla a un proveedor de IA externo:
    1. Aplica rotación EXIF para que el modelo vea la escena derecha.
    2. Reduce la resolución proporcionalmente a max_lado (ahorro de ancho de banda y tokens).
    3. Re-codifica como JPEG limpio, eliminando todo metadato EXIF/GPS (privacidad).
    Devuelve (bytes_jpeg_limpios, data_uri_base64).
    """
    limite = max_lado or settings.IA_IMAGE_MAX_SIZE
    buffer = io.BytesIO(datos)

    with Image.open(buffer) as img_raw:
        img = ImageOps.exif_transpose(img_raw) or img_raw
        if img.mode != "RGB":
            img = img.convert("RGB")

        if max(img.size) > limite:
            img.thumbnail((limite, limite), Image.Resampling.LANCZOS)

        salida = io.BytesIO()
        # Al guardar sin pasar exif=..., Pillow descarta todos los metadatos EXIF/GPS personales
        img.save(salida, format="JPEG", quality=calidad_jpeg, optimize=True)
        bytes_limpios = salida.getvalue()

    b64 = base64.b64encode(bytes_limpios).decode("ascii")
    return bytes_limpios, f"data:image/jpeg;base64,{b64}"
