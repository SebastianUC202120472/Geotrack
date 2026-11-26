import io
import os
import tempfile
import unittest
from PIL import Image, ImageDraw
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core import config
from app.db.database import Base
from app.db import solo_lectura_core
from app.models.analisis import EvidenciaAnalisis
from app.models.cola import ColaTrabajo
from app.services.worker_auditoria import ejecutar_ciclo_auditoria
from app.services.motor_auditoria import procesar_auditoria_deterministica


def _guardar_jpeg_nitido(ruta: str):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    img = Image.new("RGB", (600, 600), color="white")
    draw = ImageDraw.Draw(img)
    draw.rectangle([60, 80, 260, 480], fill="brown", outline="black", width=3)
    draw.rectangle([300, 280, 540, 520], fill="gray", outline="black", width=3)
    for y in range(0, 600, 25):
        draw.line([(0, y), (600, y)], fill="black")
    img.save(ruta, format="JPEG", quality=92)


def _guardar_jpeg_negro(ruta: str):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    img = Image.new("RGB", (500, 500), color="black")
    img.save(ruta, format="JPEG")


class TestWorkerAuditoria(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.orig_uploads = config.settings.UPLOADS_DIR
        config.settings.UPLOADS_DIR = self.tmpdir.name

        self.engine = create_engine(
            "sqlite:///:memory:",
            execution_options={"schema_translate_map": {"auditoria": None}},
        )
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()
        Base.metadata.create_all(bind=self.engine)

        # Tablas del núcleo simuladas (solo lectura)
        self.db.execute(text("""
            CREATE TABLE pedidos (
                id INTEGER PRIMARY KEY,
                codigo VARCHAR(20),
                direccion_destino VARCHAR(255),
                distrito VARCHAR(100),
                latitud FLOAT,
                longitud FLOAT,
                estado VARCHAR(50)
            )
        """))
        self.db.execute(text("""
            CREATE TABLE ruta_detalles (
                id INTEGER PRIMARY KEY,
                ruta_id INTEGER,
                pedido_id INTEGER
            )
        """))
        self.db.execute(text("""
            CREATE TABLE rutas (
                id INTEGER PRIMARY KEY,
                conductor_id INTEGER
            )
        """))
        self.db.execute(text("""
            CREATE TABLE usuarios (
                id INTEGER PRIMARY KEY,
                nombre VARCHAR(120),
                correo VARCHAR(100)
            )
        """))
        self.db.execute(text("""
            CREATE TABLE evidencias_entrega (
                id INTEGER PRIMARY KEY,
                pedido_id INTEGER,
                url_foto VARCHAR(255),
                url_firma VARCHAR(255),
                latitud_longitud_captura VARCHAR(60),
                receptor_nombre VARCHAR(120),
                receptor_documento VARCHAR(12),
                fecha_hora DATETIME
            )
        """))
        self.db.commit()

    def tearDown(self):
        self.db.close()
        config.settings.UPLOADS_DIR = self.orig_uploads
        self.tmpdir.cleanup()

    def test_ciclo_completo_worker_y_sin_duplicados_en_ruta_reasignada(self):
        # Pedido que pasó por 2 rutas (ruta 1 falló, ruta 2 entregó): no debe duplicar la evidencia
        self.db.execute(text("INSERT INTO usuarios (id, nombre, correo) VALUES (1, 'Conductor Uno', 'c1@test.pe')"))
        self.db.execute(text("INSERT INTO usuarios (id, nombre, correo) VALUES (2, 'Conductor Dos', 'c2@test.pe')"))
        self.db.execute(text("INSERT INTO rutas (id, conductor_id) VALUES (100, 1)"))
        self.db.execute(text("INSERT INTO rutas (id, conductor_id) VALUES (200, 2)"))
        self.db.execute(text("""
            INSERT INTO pedidos (id, codigo, direccion_destino, distrito, latitud, longitud, estado)
            VALUES (10, 'PD-010', 'Av. Pardo 123', 'Miraflores', -12.1190, -77.0300, 'ENTREGADO')
        """))
        self.db.execute(text("INSERT INTO ruta_detalles (id, ruta_id, pedido_id) VALUES (1, 100, 10)"))
        self.db.execute(text("INSERT INTO ruta_detalles (id, ruta_id, pedido_id) VALUES (2, 200, 10)"))
        self.db.execute(text("""
            INSERT INTO evidencias_entrega (id, pedido_id, url_foto, latitud_longitud_captura, fecha_hora)
            VALUES (50, 10, '/media/evidencias/pod_200_10.jpg', '-12.1192,-77.0301', '2026-11-17 15:00:00')
        """))
        self.db.commit()

        # Verificar que solo_lectura_core devuelve 1 sola fila y corresponde a la ruta más reciente (200)
        recientes = solo_lectura_core.obtener_evidencias_recientes(self.db)
        self.assertEqual(len(recientes), 1)
        self.assertEqual(recientes[0]["ruta_id"], 200)
        self.assertEqual(recientes[0]["conductor_id"], 2)

        # Guardar imagen física en el volumen simulado
        _guardar_jpeg_nitido(os.path.join(self.tmpdir.name, "evidencias", "pod_200_10.jpg"))

        # Ejecutar ciclo punta a punta del worker
        resumen = ejecutar_ciclo_auditoria(self.db)
        self.assertEqual(resumen, {"encoladas": 1, "procesadas": 1, "fallidas": 0})

        tarea = self.db.query(ColaTrabajo).filter_by(evidencia_id=50).first()
        self.assertEqual(tarea.estado, "COMPLETADO")

        analisis = self.db.query(EvidenciaAnalisis).filter_by(evidencia_id=50).first()
        self.assertIsNotNone(analisis)
        self.assertEqual(analisis.semaforo, "verde")
        self.assertIsNotNone(analisis.distancia_gps_metros)
        self.assertLess(analisis.distancia_gps_metros, 100.0)

    def test_worker_archivo_faltante_reintenta_con_backoff(self):
        self.db.execute(text("INSERT INTO pedidos (id, codigo, direccion_destino) VALUES (11, 'PD-011', 'Calle X')"))
        self.db.execute(text("""
            INSERT INTO evidencias_entrega (id, pedido_id, url_foto)
            VALUES (51, 11, '/media/evidencias/inexistente.jpg')
        """))
        self.db.commit()

        resumen = ejecutar_ciclo_auditoria(self.db)
        self.assertEqual(resumen["encoladas"], 1)
        self.assertEqual(resumen["procesadas"], 0)
        self.assertEqual(resumen["fallidas"], 1)

        tarea = self.db.query(ColaTrabajo).filter_by(evidencia_id=51).first()
        self.assertEqual(tarea.estado, "PENDIENTE")
        self.assertEqual(tarea.intentos, 1)
        self.assertIn("No se pudo leer", tarea.ultimo_error)

    def test_worker_detecta_foto_reemplazada_en_misma_evidencia(self):
        self.db.execute(text("INSERT INTO pedidos (id, codigo, direccion_destino) VALUES (12, 'PD-012', 'Av. Sur')"))
        self.db.execute(text("""
            INSERT INTO evidencias_entrega (id, pedido_id, url_foto)
            VALUES (52, 12, '/media/evidencias/pod_v1.jpg')
        """))
        self.db.commit()

        _guardar_jpeg_nitido(os.path.join(self.tmpdir.name, "evidencias", "pod_v1.jpg"))
        res1 = ejecutar_ciclo_auditoria(self.db)
        self.assertEqual(res1["procesadas"], 1)

        # Conductor sobrescribe la foto del mismo registro evidencias_entrega.id=52 con una foto negra
        _guardar_jpeg_negro(os.path.join(self.tmpdir.name, "evidencias", "pod_v2.jpg"))
        self.db.execute(text("UPDATE evidencias_entrega SET url_foto = '/media/evidencias/pod_v2.jpg' WHERE id = 52"))
        self.db.commit()

        res2 = ejecutar_ciclo_auditoria(self.db)
        self.assertEqual(res2["encoladas"], 1)
        self.assertEqual(res2["procesadas"], 1)

        analisis_v2 = self.db.query(EvidenciaAnalisis).filter_by(
            evidencia_id=52, url_foto="/media/evidencias/pod_v2.jpg"
        ).first()
        self.assertIsNotNone(analisis_v2)
        self.assertEqual(analisis_v2.semaforo, "rojo")

    def test_upsert_idempotente_cuando_falla_validacion_archivo(self):
        procesar_auditoria_deterministica(
            db=self.db,
            evidencia_id=99,
            pedido_id=99,
            url_foto="/media/evidencias/corrupto.jpg",
            datos_imagen=b"no-es-una-imagen",
        )
        procesar_auditoria_deterministica(
            db=self.db,
            evidencia_id=99,
            pedido_id=99,
            url_foto="/media/evidencias/corrupto.jpg",
            datos_imagen=b"no-es-una-imagen",
        )
        total = self.db.query(EvidenciaAnalisis).filter_by(
            evidencia_id=99, url_foto="/media/evidencias/corrupto.jpg"
        ).count()
        self.assertEqual(total, 1)


if __name__ == "__main__":
    unittest.main()
