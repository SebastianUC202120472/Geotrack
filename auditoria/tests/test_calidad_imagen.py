import io
import unittest
from PIL import Image, ImageDraw

from app.services.calidad_imagen import evaluar_calidad_imagen


def generar_imagen_nitida(ancho=400, alto=400):
    """Genera una imagen con alto contraste y patrones geométricos (nítida)."""
    img = Image.new("RGB", (ancho, alto), color="white")
    draw = ImageDraw.Draw(img)
    for i in range(0, ancho, 20):
        draw.line([(i, 0), (i, alto)], fill="black", width=3)
        draw.line([(0, i), (ancho, i)], fill="black", width=3)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def generar_imagen_plana_borrosa(ancho=400, alto=400):
    """Genera una imagen plana/lisa sin bordes (simula borrosidad total o lente tapado)."""
    img = Image.new("RGB", (ancho, alto), color=(128, 128, 128))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def generar_imagen_oscura(ancho=400, alto=400):
    """Genera una imagen casi negra."""
    img = Image.new("RGB", (ancho, alto), color=(10, 10, 10))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def generar_imagen_quemada(ancho=400, alto=400):
    """Genera una imagen sobreexpuesta/quemada."""
    img = Image.new("RGB", (ancho, alto), color=(250, 250, 250))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def generar_imagen_diminuta():
    """Genera una imagen de 100x100 (inferior a los 300x300 mínimos)."""
    img = Image.new("RGB", (100, 100), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


class TestCalidadImagen(unittest.TestCase):
    def test_imagen_nitida(self):
        datos = generar_imagen_nitida()
        res = evaluar_calidad_imagen(datos)
        self.assertFalse(res.es_borrosa)
        self.assertFalse(res.es_oscura)
        self.assertFalse(res.es_sobreexpuesta)
        self.assertFalse(res.resolucion_baja)
        self.assertGreater(res.varianza_laplaciana, 40.0)
        self.assertGreaterEqual(res.calidad_score, 0.9)

    def test_imagen_borrosa(self):
        datos = generar_imagen_plana_borrosa()
        res = evaluar_calidad_imagen(datos)
        self.assertTrue(res.es_borrosa)
        self.assertLess(res.varianza_laplaciana, 40.0)
        self.assertLess(res.calidad_score, 0.7)

    def test_imagen_oscura(self):
        datos = generar_imagen_oscura()
        res = evaluar_calidad_imagen(datos)
        self.assertTrue(res.es_oscura)
        self.assertLess(res.brillo_promedio, 45.0)

    def test_imagen_quemada(self):
        datos = generar_imagen_quemada()
        res = evaluar_calidad_imagen(datos)
        self.assertTrue(res.es_sobreexpuesta)
        self.assertGreater(res.brillo_promedio, 235.0)

    def test_resolucion_baja(self):
        datos = generar_imagen_diminuta()
        res = evaluar_calidad_imagen(datos)
        self.assertTrue(res.resolucion_baja)
        self.assertEqual(res.resolucion_ancho, 100)
        self.assertEqual(res.resolucion_alto, 100)


if __name__ == "__main__":
    unittest.main()
