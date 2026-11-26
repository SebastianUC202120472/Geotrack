import io
import unittest
from datetime import datetime, timedelta
from PIL import Image

from app.services.validador_exif import (
    calcular_distancia_haversine,
    validar_exif_espaciotemporal,
)


def crear_imagen_con_exif_fecha(fecha_str="2026:11:17 14:30:00"):
    img = Image.new("RGB", (200, 200), color="white")
    exif = img.getexif()
    # Tag 36867 = DateTimeOriginal, 306 = DateTime
    exif[306] = fecha_str
    exif[36867] = fecha_str
    buf = io.BytesIO()
    img.save(buf, format="JPEG", exif=exif)
    return buf.getvalue()


class TestValidadorEXIF(unittest.TestCase):
    def test_distancia_haversine_calculo(self):
        # Dos puntos en Lima cercanos (aprox 140 metros)
        # Punto A: Plaza Mayor (-12.046374, -77.030588)
        # Punto B: Palacio de Gobierno (-12.045330, -77.029800)
        dist = calcular_distancia_haversine(-12.046374, -77.030588, -12.045330, -77.029800)
        self.assertGreater(dist, 100.0)
        self.assertLess(dist, 200.0)

    def test_imagen_sin_exif_pero_gps_app_cercano(self):
        # Foto sin EXIF (típica de app móvil comprimida), GPS de app a 50 metros del destino
        img = Image.new("RGB", (200, 200), color="white")
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        datos = buf.getvalue()

        # Destino: -12.0460, -77.0300
        # Captura: -12.0463, -77.0302 (~40 m de distancia)
        res = validar_exif_espaciotemporal(
            datos=datos,
            fecha_declarada=datetime.utcnow(),
            pedido_latitud=-12.0460,
            pedido_longitud=-77.0300,
            captura_gps_app="-12.0463,-77.0302",
        )
        self.assertFalse(res.tiene_exif)
        self.assertFalse(res.alerta_gps)
        self.assertIsNotNone(res.distancia_gps_metros)
        self.assertLess(res.distancia_gps_metros, 350.0)

    def test_imagen_gps_app_muy_lejano_alerta(self):
        # Foto tomada a más de 2 km de distancia
        img = Image.new("RGB", (200, 200), color="white")
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        datos = buf.getvalue()

        res = validar_exif_espaciotemporal(
            datos=datos,
            fecha_declarada=datetime.utcnow(),
            pedido_latitud=-12.0460,
            pedido_longitud=-77.0300,
            captura_gps_app="-12.0700,-77.0500",  # ~3.5 km de distancia
        )
        self.assertTrue(res.alerta_gps)
        self.assertGreater(res.distancia_gps_metros, 1000.0)
        self.assertIn("Distancia excesiva", res.motivo_alerta)

    def test_exif_fecha_coincidente(self):
        ahora = datetime(2026, 11, 17, 14, 30, 0)
        datos = crear_imagen_con_exif_fecha("2026:11:17 14:32:00")  # 2 minutos de desfase

        res = validar_exif_espaciotemporal(
            datos=datos,
            fecha_declarada=ahora,
        )
        self.assertTrue(res.tiene_exif)
        self.assertFalse(res.alerta_fecha)
        self.assertEqual(res.desfase_temporal_minutos, 2.0)

    def test_exif_fecha_antigua_alerta(self):
        # Foto tomada hace 1 año pretendiendo ser de hoy
        ahora = datetime(2026, 11, 17, 14, 30, 0)
        datos = crear_imagen_con_exif_fecha("2025:11:17 14:30:00")

        res = validar_exif_espaciotemporal(
            datos=datos,
            fecha_declarada=ahora,
        )
        self.assertTrue(res.tiene_exif)
        self.assertTrue(res.alerta_fecha)
        self.assertGreater(res.desfase_temporal_minutos, 50000.0)
        self.assertIn("Desfase horario", res.motivo_alerta)


if __name__ == "__main__":
    unittest.main()
