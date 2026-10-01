import io

import pytest
from fastapi import HTTPException
from PIL import Image

from app.core import imagenes
from app.core.config import settings


def _imagen(formato: str) -> bytes:
    salida = io.BytesIO()
    Image.new("RGB", (20, 20), "red").save(salida, format=formato)
    return salida.getvalue()


@pytest.mark.parametrize("formato,extension", [("JPEG", ".jpg"), ("PNG", ".png"), ("WEBP", ".webp")])
def test_acepta_imagenes_reales_y_devuelve_su_extension(formato, extension):
    assert imagenes.validar_imagen(_imagen(formato)) == extension


@pytest.mark.parametrize("contenido", [
    b"",
    b"<?php system($_GET['c']); ?>",          # script renombrado a .jpg
    b"\xff\xd8\xff\xe0" + b"basura" * 50,     # solo la cabecera de un JPEG
    b"%PDF-1.4 no soy una imagen",
])
def test_rechaza_lo_que_no_es_imagen(contenido):
    with pytest.raises(HTTPException) as error:
        imagenes.validar_imagen(contenido)
    assert error.value.status_code == 400


def test_rechaza_formato_de_imagen_no_permitido():
    """Un GIF es una imagen real, pero no esta en la lista permitida."""
    with pytest.raises(HTTPException) as error:
        imagenes.validar_imagen(_imagen("GIF"))
    assert error.value.status_code == 400


def test_rechaza_imagen_que_supera_el_tamano_maximo(monkeypatch):
    monkeypatch.setattr(settings, "IMAGEN_MAX_MB", 0)
    with pytest.raises(HTTPException) as error:
        imagenes.validar_imagen(_imagen("PNG"))
    assert error.value.status_code == 413
