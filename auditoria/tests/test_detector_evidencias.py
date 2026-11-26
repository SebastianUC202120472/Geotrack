import unittest
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.core import config
from app.models.analisis import EvidenciaAnalisis
from app.models.cola import ColaTrabajo
from app.services import detector_evidencias


class TestDetectorEvidencias(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite:///:memory:",
            execution_options={"schema_translate_map": {"auditoria": None}}
        )
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()

        # Crear tablas del módulo auditoría
        Base.metadata.create_all(bind=self.engine)

        # Crear tablas simuladas del núcleo
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

    def test_sincronizacion_nuevas_evidencias(self):
        # Insertar pedido y evidencia en el núcleo
        self.db.execute(text("INSERT INTO pedidos (id, codigo, direccion_destino) VALUES (1, 'PD-101', 'Av Lima 123')"))
        self.db.execute(text("INSERT INTO evidencias_entrega (id, pedido_id, url_foto) VALUES (10, 1, '/media/evidencias/foto1.jpg')"))
        self.db.commit()

        encoladas = detector_evidencias.sincronizar_nuevas_evidencias(self.db)
        self.assertEqual(encoladas, 1)

        tarea = detector_evidencias.obtener_siguiente_tarea(self.db)
        self.assertIsNotNone(tarea)
        self.assertEqual(tarea.evidencia_id, 10)
        self.assertEqual(tarea.estado, "PENDIENTE")

    def test_tope_diario_respetado(self):
        # Fijar tope diario en 1
        orig_tope = config.settings.AUDITORIA_TOPE_DIARIO
        try:
            config.settings.AUDITORIA_TOPE_DIARIO = 1

            # Insertar un análisis ya realizado hoy
            analisis = EvidenciaAnalisis(
                evidencia_id=99,
                pedido_id=1,
                url_foto="/media/test.jpg",
                sha256="abc",
                semaforo="verde",
            )
            self.db.add(analisis)
            self.db.commit()

            # Insertar nueva evidencia no analizada
            self.db.execute(text("INSERT INTO pedidos (id, codigo, direccion_destino) VALUES (2, 'PD-102', 'Av Arequipa')"))
            self.db.execute(text("INSERT INTO evidencias_entrega (id, pedido_id, url_foto) VALUES (20, 2, '/media/evidencias/foto2.jpg')"))
            self.db.commit()

            encoladas = detector_evidencias.sincronizar_nuevas_evidencias(self.db)
            self.assertEqual(encoladas, 0)
        finally:
            config.settings.AUDITORIA_TOPE_DIARIO = orig_tope

    def test_reintento_con_backoff(self):
        item = ColaTrabajo(evidencia_id=30, pedido_id=3, url_foto="/media/foto3.jpg", estado="PROCESANDO")
        self.db.add(item)
        self.db.commit()

        # Primer fallo -> reintentará
        detector_evidencias.registrar_fallo_cola(self.db, item.id, "Error de red temporal")
        self.db.refresh(item)
        self.assertEqual(item.intentos, 1)
        self.assertEqual(item.estado, "PENDIENTE")
        self.assertTrue(item.programado_para > datetime.utcnow())

        # Superar max reintentos -> FALLIDO
        detector_evidencias.registrar_fallo_cola(self.db, item.id, "Fallo 2")
        detector_evidencias.registrar_fallo_cola(self.db, item.id, "Fallo 3")
        self.db.refresh(item)
        self.assertEqual(item.intentos, 3)
        self.assertEqual(item.estado, "FALLIDO")


if __name__ == "__main__":
    unittest.main()
