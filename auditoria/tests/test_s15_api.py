import os
import tempfile
import unittest
from datetime import datetime, timedelta
import httpx
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core import config
from app.db.database import Base, get_db
from app.main import app
from app.api.deps import limpiar_cache_identidad
from app.models.analisis import EvidenciaAnalisis
from app.models.cola import ColaTrabajo
from app.models.revision import RevisionHumana
from app.services.motor_auditoria import procesar_auditoria_deterministica


def _crear_jpeg_bytes(ruta: str | None = None, color="white", nitido=True) -> bytes:
    img = Image.new("RGB", (500, 500), color=color)
    if nitido:
        draw = ImageDraw.Draw(img)
        draw.rectangle([50, 50, 220, 420], fill="brown", outline="black", width=3)
        for y in range(0, 500, 25):
            draw.line([(0, y), (500, y)], fill="black")
    import io
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    datos = buf.getvalue()
    if ruta:
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        with open(ruta, "wb") as f:
            f.write(datos)
    return datos


class TestS15ApiAuditoria(unittest.TestCase):
    def setUp(self):
        limpiar_cache_identidad()
        self.tmpdir = tempfile.TemporaryDirectory()
        self.orig_uploads = config.settings.UPLOADS_DIR
        self.orig_worker = config.settings.AUDITORIA_WORKER_ENABLED
        config.settings.UPLOADS_DIR = self.tmpdir.name
        config.settings.AUDITORIA_WORKER_ENABLED = False

        # StaticPool para compartir la misma BD SQLite en memoria entre hilos de TestClient
        self.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            execution_options={"schema_translate_map": {"auditoria": None}},
        )
        self.Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)

        self.db = self.Session()
        self._crear_tablas_core_simuladas()

        def override_get_db():
            db = self.Session()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db

        # Mock de autenticación contra /usuarios/yo
        def auth_handler(request: httpx.Request) -> httpx.Response:
            auth = request.headers.get("authorization", "")
            if auth == "Bearer token-admin":
                return httpx.Response(200, json={"id": 1, "correo": "admin@sava.pe", "nombre": "Admin", "rol": "admin", "estado": True})
            if auth == "Bearer token-conductor":
                return httpx.Response(200, json={"id": 2, "correo": "chofer@sava.pe", "nombre": "Chofer", "rol": "conductor", "estado": True})
            return httpx.Response(401, json={"detail": "Inválido"})

        self.async_mock_client = httpx.AsyncClient(transport=httpx.MockTransport(auth_handler))
        app.state.http_core = self.async_mock_client
        self.client = TestClient(app)

    def tearDown(self):
        self.db.close()
        app.dependency_overrides.clear()
        limpiar_cache_identidad()
        config.settings.UPLOADS_DIR = self.orig_uploads
        config.settings.AUDITORIA_WORKER_ENABLED = self.orig_worker
        self.tmpdir.cleanup()

    def _crear_tablas_core_simuladas(self):
        for ddl in [
            "CREATE TABLE pedidos (id INTEGER PRIMARY KEY, codigo VARCHAR(20), direccion_destino VARCHAR(255), distrito VARCHAR(100), latitud FLOAT, longitud FLOAT, estado VARCHAR(50))",
            "CREATE TABLE ruta_detalles (id INTEGER PRIMARY KEY, ruta_id INTEGER, pedido_id INTEGER)",
            "CREATE TABLE rutas (id INTEGER PRIMARY KEY, conductor_id INTEGER)",
            "CREATE TABLE usuarios (id INTEGER PRIMARY KEY, nombre VARCHAR(120), correo VARCHAR(100))",
            "CREATE TABLE evidencias_entrega (id INTEGER PRIMARY KEY, pedido_id INTEGER, url_foto VARCHAR(255), url_firma VARCHAR(255), latitud_longitud_captura VARCHAR(60), receptor_nombre VARCHAR(120), receptor_documento VARCHAR(12), fecha_hora DATETIME)",
            "CREATE TABLE reclamos (id INTEGER PRIMARY KEY, codigo VARCHAR(20), tipo VARCHAR(10), detalle TEXT, pedido_codigo VARCHAR(20), creado_en DATETIME)",
        ]:
            self.db.execute(text(ddl))
        self.db.commit()

    def test_salud_y_control_acceso_admin(self):
        r_salud = self.client.get("/api/auditoria/salud")
        self.assertEqual(r_salud.status_code, 200)
        self.assertTrue(r_salud.json()["activo"])

        # Sin token -> 401
        self.assertEqual(self.client.get("/api/auditoria/evidencias").status_code, 401)
        # Conductor -> 403
        self.assertEqual(
            self.client.get("/api/auditoria/evidencias", headers={"Authorization": "Bearer token-conductor"}).status_code,
            403,
        )
        # Admin -> 200
        self.assertEqual(
            self.client.get("/api/auditoria/evidencias", headers={"Authorization": "Bearer token-admin"}).status_code,
            200,
        )

    def test_cola_reclamos_imagen_dictamen_y_metricas(self):
        # Seed núcleo solo lectura
        self.db.execute(text("INSERT INTO usuarios (id, nombre, correo) VALUES (10, 'Juan Pérez', 'juan@sava.pe')"))
        self.db.execute(text("INSERT INTO rutas (id, conductor_id) VALUES (1, 10)"))
        self.db.execute(text("INSERT INTO pedidos (id, codigo, direccion_destino, distrito, estado) VALUES (1, 'PD-001', 'Av A 100', 'Lima', 'ENTREGADO')"))
        self.db.execute(text("INSERT INTO pedidos (id, codigo, direccion_destino, distrito, estado) VALUES (2, 'PD-002', 'Av B 200', 'Surco', 'ENTREGADO')"))
        self.db.execute(text("INSERT INTO ruta_detalles (id, ruta_id, pedido_id) VALUES (1, 1, 1)"))
        self.db.execute(text("INSERT INTO ruta_detalles (id, ruta_id, pedido_id) VALUES (2, 1, 2)"))
        self.db.execute(text("INSERT INTO evidencias_entrega (id, pedido_id, url_foto) VALUES (100, 1, '/media/evidencias/ok.jpg')"))
        self.db.execute(text("INSERT INTO evidencias_entrega (id, pedido_id, url_foto) VALUES (101, 2, '/media/evidencias/alerta.jpg')"))
        self.db.execute(text("INSERT INTO reclamos (id, codigo, tipo, detalle, pedido_codigo) VALUES (1, 'LR-2026-0001', 'RECLAMO', 'No me entregaron el paquete', 'PD-001')"))
        self.db.commit()

        _crear_jpeg_bytes(os.path.join(self.tmpdir.name, "evidencias", "ok.jpg"))
        _crear_jpeg_bytes(os.path.join(self.tmpdir.name, "evidencias", "alerta.jpg"), color="black", nitido=False)

        a1 = EvidenciaAnalisis(evidencia_id=100, pedido_id=1, url_foto="/media/evidencias/ok.jpg", sha256="h1", semaforo="verde", calidad_score=0.95)
        a2 = EvidenciaAnalisis(evidencia_id=101, pedido_id=2, url_foto="/media/evidencias/alerta.jpg", sha256="h2", semaforo="rojo", motivo_alerta="Imagen oscura", calidad_score=0.2)
        self.db.add_all([a1, a2])
        self.db.commit()
        self.db.refresh(a1)
        self.db.refresh(a2)

        hdr = {"Authorization": "Bearer token-admin"}

        # 1. Listado prioriza reclamo activo (PD-001)
        r_lista = self.client.get("/api/auditoria/evidencias", headers=hdr)
        self.assertEqual(r_lista.status_code, 200)
        items = r_lista.json()
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["pedido_codigo"], "PD-001")
        self.assertTrue(items[0]["tiene_reclamo"])

        # 2. Filtro solo_con_reclamo
        r_rec = self.client.get("/api/auditoria/evidencias?solo_con_reclamo=true", headers=hdr)
        self.assertEqual(len(r_rec.json()), 1)

        # 3. Imagen autenticada
        self.assertEqual(self.client.get(f"/api/auditoria/evidencias/{a1.id}/imagen").status_code, 401)
        r_img = self.client.get(f"/api/auditoria/evidencias/{a1.id}/imagen", headers=hdr)
        self.assertEqual(r_img.status_code, 200)
        self.assertEqual(r_img.headers["content-type"], "image/jpeg")

        # 4. Dictamen humano (OBSERVADA requiere motivo)
        r_bad = self.client.post(f"/api/auditoria/evidencias/{a2.id}/dictamen", json={"dictamen": "OBSERVADA", "motivo": ""}, headers=hdr)
        self.assertEqual(r_bad.status_code, 400)

        r_obs = self.client.post(
            f"/api/auditoria/evidencias/{a2.id}/dictamen",
            json={"dictamen": "OBSERVADA", "motivo": "Foto completamente negra"},
            headers=hdr,
        )
        self.assertEqual(r_obs.status_code, 200)
        self.assertEqual(r_obs.json()["admin_email"], "admin@sava.pe")

        # Marcar a1 como VALIDA (aunque tenia reclamo, admin valida entrega)
        self.client.post(f"/api/auditoria/evidencias/{a1.id}/dictamen", json={"dictamen": "VALIDA"}, headers=hdr)

        # 5. Métricas y reincidencia por conductor
        r_met = self.client.get("/api/auditoria/metricas", headers=hdr)
        self.assertEqual(r_met.status_code, 200)
        met = r_met.json()
        self.assertEqual(met["total_analizadas"], 2)
        self.assertEqual(met["total_observadas"], 1)
        self.assertEqual(met["porcentaje_observadas"], 50.0)
        self.assertEqual(met["reincidencia_conductores"][0]["conductor_nombre"], "Juan Pérez")
        self.assertEqual(met["reincidencia_conductores"][0]["total_observadas"], 1)

    def test_retencion_purga_solo_antiguos(self):
        antiguo = EvidenciaAnalisis(
            evidencia_id=200,
            pedido_id=20,
            url_foto="/media/antigua.jpg",
            sha256="old",
            semaforo="verde",
            creado_en=datetime.utcnow() - timedelta(days=120),
        )
        reciente = EvidenciaAnalisis(
            evidencia_id=201,
            pedido_id=21,
            url_foto="/media/reciente.jpg",
            sha256="new",
            semaforo="verde",
            creado_en=datetime.utcnow(),
        )
        self.db.add_all([antiguo, reciente])
        self.db.commit()

        r = self.client.post(
            "/api/auditoria/retencion/purgar?dias=90",
            headers={"Authorization": "Bearer token-admin"},
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["analisis_eliminados"], 1)
        self.assertEqual(self.db.query(EvidenciaAnalisis).count(), 1)

    def test_endpoint_sembrar_demo(self):
        r = self.client.post("/api/auditoria/demo", headers={"Authorization": "Bearer token-admin"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["evidencias_demo_analizadas"], 4)
        self.assertEqual(self.db.query(EvidenciaAnalisis).count(), 4)

    def test_benchmark_aciertos_y_falsas_alarmas(self):
        """Mide aciertos y falsas alarmas sobre un lote de casos conocidos."""
        nitida = _crear_jpeg_bytes(nitido=True)
        negra = _crear_jpeg_bytes(color="black", nitido=False)
        borrosa = _crear_jpeg_bytes(color=(150, 150, 150), nitido=False)

        a_ok = procesar_auditoria_deterministica(self.db, 301, 31, "/media/b1.jpg", nitida)
        a_neg = procesar_auditoria_deterministica(self.db, 302, 32, "/media/b2.jpg", negra)
        a_bor = procesar_auditoria_deterministica(self.db, 303, 33, "/media/b3.jpg", borrosa)
        a_dup = procesar_auditoria_deterministica(self.db, 304, 34, "/media/b4.jpg", nitida)

        # Cero falsas alarmas en foto nítida, y 100% detección en negra/borrosa/duplicada
        self.assertEqual(a_ok.semaforo, "verde")
        self.assertEqual(a_neg.semaforo, "rojo")
        self.assertIn(a_bor.semaforo, ("ambar", "rojo"))
        self.assertEqual(a_dup.semaforo, "rojo")


if __name__ == "__main__":
    unittest.main()
