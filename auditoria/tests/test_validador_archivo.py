import io
import unittest
from PIL import Image

from app.services.validador_archivo import validar_archivo_seguro
from app.core import config


def crear_imagen_prueba(ancho=400, alto=400, color="blue", formato="JPEG"):
    buf = io.BytesIO()
    img = Image.new("RGB", (ancho, alto), color=color)
    img.save(buf, format=formato)
    return buf.getvalue()


class TestValidadorArchivo(unittest.TestCase):
    def test_archivo_jpeg_valido(self):
        datos = crear_imagen_prueba(formato="JPEG")
        res = validar_archivo_seguro(datos)
        self.assertTrue(res.valido)
        self.assertEqual(res.formato, "jpeg")
        self.assertEqual(res.ancho, 400)
        self.assertEqual(res.alto, 400)

    def test_archivo_png_valido(self):
        datos = crear_imagen_prueba(formato="PNG")
        res = validar_archivo_seguro(datos)
        self.assertTrue(res.valido)
        self.assertEqual(res.formato, "png")

    def test_archivo_invalido_extension_falsa(self):
        datos_falsos = b"ESTO NO ES UNA IMAGEN PERO TIENE EXTENSION .JPG"
        res = validar_archivo_seguro(datos_falsos)
        self.assertFalse(res.valido)
        self.assertIn("magic bytes", res.error)

    def test_archivo_vacio(self):
        res = validar_archivo_seguro(b"")
        self.assertFalse(res.valido)
        self.assertIn("vacío", res.error)

    def test_proteccion_bomba_descompresion(self):
        original = config.settings.MAX_PIXELS
        try:
            config.settings.MAX_PIXELS = 50000
            datos = crear_imagen_prueba(ancho=300, alto=300, formato="JPEG")  # 90,000 > 50,000
            res = validar_archivo_seguro(datos)
            self.assertFalse(res.valido)
            self.assertTrue(res.es_bomba_descompresion)
        finally:
            config.settings.MAX_PIXELS = original


if __name__ == "__main__":
    unittest.main()
