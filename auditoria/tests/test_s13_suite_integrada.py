import io
import unittest
from datetime import datetime, timedelta
from PIL import Image, ImageDraw
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.services.motor_auditoria import procesar_auditoria_deterministica
from app.core import config


def generar_imagen_entrega_nitida():
    img = Image.new("RGB", (600, 600), color="white")
    draw = ImageDraw.Draw(img)
    # Dibujar detalles que simulan fachada y paquete (bordes y colores)
    draw.rectangle([50, 100, 250, 500], fill="brown", outline="black", width=2)
    draw.rectangle([300, 300, 550, 550], fill="darkgray", outline="black", width=2)
    for y in range(0, 600, 30):
        draw.line([(0, y), (600, y)], fill="lightgray")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return img, buf.getvalue()


def generar_imagen_borrosa():
    img = Image.new("RGB", (500, 500), color=(150, 150, 150))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def generar_imagen_totalmente_negra():
    img = Image.new("RGB", (500, 500), color="black")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


class TestS13SuiteIntegrada(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite:///:memory:",
            execution_options={"schema_translate_map": {"auditoria": None}}
        )
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()
        Base.metadata.create_all(bind=self.engine)

    def tearDown(self):
        self.db.close()

    def test_evidencia_genuina_valida(self):
        _, datos = generar_imagen_entrega_nitida()
        ahora = datetime.utcnow()

        analisis = procesar_auditoria_deterministica(
            db=self.db,
            evidencia_id=1,
            pedido_id=10,
            url_foto="/media/evidencias/pod_1_10.jpg",
            datos_imagen=datos,
            fecha_entrega_declarada=ahora,
            pedido_latitud=-12.0460,
            pedido_longitud=-77.0300,
            captura_gps_app="-12.0462,-77.0301",  # ~30m de distancia
        )

        self.assertEqual(analisis.semaforo, "verde")
        self.assertFalse(analisis.es_borrosa)
        self.assertFalse(analisis.es_oscura)
        self.assertFalse(analisis.es_duplicada)
        self.assertFalse(analisis.alerta_gps)
        self.assertGreaterEqual(analisis.calidad_score, 0.9)

    def test_evidencia_borrosa_alerta(self):
        datos = generar_imagen_borrosa()
        analisis = procesar_auditoria_deterministica(
            db=self.db,
            evidencia_id=2,
            pedido_id=11,
            url_foto="/media/evidencias/pod_2_11.jpg",
            datos_imagen=datos,
        )

        self.assertTrue(analisis.es_borrosa)
        self.assertIn(analisis.semaforo, ("ambar", "rojo"))
        self.assertIn("borrosa", analisis.motivo_alerta.lower())

    def test_evidencia_oscura_extrema_rojo(self):
        datos = generar_imagen_totalmente_negra()
        analisis = procesar_auditoria_deterministica(
            db=self.db,
            evidencia_id=3,
            pedido_id=12,
            url_foto="/media/evidencias/pod_3_12.jpg",
            datos_imagen=datos,
        )

        self.assertTrue(analisis.es_oscura)
        self.assertEqual(analisis.semaforo, "rojo")
        self.assertIn("oscura", analisis.motivo_alerta.lower())

    def test_evidencia_reciclada_rojo(self):
        img_original, datos_original = generar_imagen_entrega_nitida()

        # 1. Procesar primera evidencia genuina
        procesar_auditoria_deterministica(
            db=self.db,
            evidencia_id=4,
            pedido_id=13,
            url_foto="/media/evidencias/pod_4_13.jpg",
            datos_imagen=datos_original,
        )

        # 2. Conductor intenta reciclar la misma imagen en otro pedido, reescalándola ligeramente
        img_reciclada = img_original.resize((450, 450), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        img_reciclada.save(buf, format="JPEG", quality=85)
        datos_reciclada = buf.getvalue()

        analisis_dup = procesar_auditoria_deterministica(
            db=self.db,
            evidencia_id=5,
            pedido_id=14,
            url_foto="/media/evidencias/pod_5_14.jpg",
            datos_imagen=datos_reciclada,
        )

        self.assertTrue(analisis_dup.es_duplicada)
        self.assertEqual(analisis_dup.duplicada_con_evidencia_id, 4)
        self.assertEqual(analisis_dup.semaforo, "rojo")
        self.assertIn("reciclada", analisis_dup.motivo_alerta.lower())

    def test_evidencia_gps_lejano_alerta(self):
        _, datos = generar_imagen_entrega_nitida()

        analisis = procesar_auditoria_deterministica(
            db=self.db,
            evidencia_id=6,
            pedido_id=15,
            url_foto="/media/evidencias/pod_6_15.jpg",
            datos_imagen=datos,
            pedido_latitud=-12.0460,
            pedido_longitud=-77.0300,
            captura_gps_app="-12.0800,-77.0600",  # ~5 km de distancia
        )

        self.assertTrue(analisis.alerta_gps)
        self.assertEqual(analisis.semaforo, "ambar")
        self.assertIn("distancia excesiva", analisis.motivo_alerta.lower())

    def test_evidencia_archivo_falso_rojo(self):
        datos_falsos = b"ESTO_ES_UN_SCRIPT_MALICIOSO.SH"

        analisis = procesar_auditoria_deterministica(
            db=self.db,
            evidencia_id=7,
            pedido_id=16,
            url_foto="/media/evidencias/pod_7_16.jpg",
            datos_imagen=datos_falsos,
        )

        self.assertEqual(analisis.semaforo, "rojo")
        self.assertEqual(analisis.calidad_score, 0.0)
        self.assertIn("no seguro o inválido", analisis.motivo_alerta.lower())


if __name__ == "__main__":
    unittest.main()
