import io
import unittest
from PIL import Image, ImageDraw
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.models.analisis import EvidenciaAnalisis
from app.services.hash_perceptual import (
    calcular_sha256,
    calcular_perceptual_hash,
    distancia_hamming,
    buscar_foto_reciclada,
)


def crear_imagen_base():
    img = Image.new("RGB", (400, 400), color="white")
    draw = ImageDraw.Draw(img)
    for i in range(0, 400, 40):
        draw.rectangle([i, i, i + 20, i + 20], fill="black")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return img, buf.getvalue()


def crear_imagen_diferente():
    img = Image.new("RGB", (400, 400), color="black")
    draw = ImageDraw.Draw(img)
    draw.ellipse([50, 50, 350, 350], fill="white")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


class TestHashPerceptual(unittest.TestCase):
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

    def test_sha256_consistente(self):
        datos = b"prueba_de_bytes"
        hash1 = calcular_sha256(datos)
        hash2 = calcular_sha256(datos)
        self.assertEqual(hash1, hash2)
        self.assertEqual(len(hash1), 64)

    def test_distancia_hamming_identica(self):
        h1 = "a1b2c3d4e5f60718"
        self.assertEqual(distancia_hamming(h1, h1), 0)

    def test_distancia_hamming_diferente(self):
        h1 = "0000000000000000"
        h2 = "000000000000000f"  # 'f' tiene 4 bits en '1'
        self.assertEqual(distancia_hamming(h1, h2), 4)

    def test_perceptual_hash_mismo_contenido_diferente_escala(self):
        img_raw, datos_original = crear_imagen_base()

        # Misma imagen escalada a la mitad y recomprimida con menos calidad
        img_escalada = img_raw.resize((200, 200), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        img_escalada.save(buf, format="JPEG", quality=70)
        datos_escalada = buf.getvalue()

        h_orig = calcular_perceptual_hash(datos_original)
        h_esc = calcular_perceptual_hash(datos_escalada)

        dist = distancia_hamming(h_orig, h_esc)
        # La distancia entre la misma imagen a distinta escala y compresión debe ser <= 3
        self.assertLessEqual(dist, 3)

    def test_perceptual_hash_imagenes_diferentes(self):
        _, datos_base = crear_imagen_base()
        datos_dif = crear_imagen_diferente()

        h1 = calcular_perceptual_hash(datos_base)
        h2 = calcular_perceptual_hash(datos_dif)

        dist = distancia_hamming(h1, h2)
        # Imágenes totalmente distintas deben tener una distancia significativa (> 20)
        self.assertGreater(dist, 20)

    def test_buscar_foto_reciclada_en_db(self):
        img_raw, datos_original = crear_imagen_base()
        h_orig = calcular_perceptual_hash(datos_original)
        sha_orig = calcular_sha256(datos_original)

        # Guardar primer análisis en BD
        previo = EvidenciaAnalisis(
            evidencia_id=101,
            pedido_id=1,
            url_foto="/media/foto_original.jpg",
            sha256=sha_orig,
            perceptual_hash=h_orig,
            semaforo="verde",
        )
        self.db.add(previo)
        self.db.commit()

        # Nueva evidencia con foto ligeramente re-escalada (reciclada)
        img_reciclada = img_raw.resize((250, 250), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        img_reciclada.save(buf, format="JPEG", quality=80)
        datos_reciclada = buf.getvalue()

        h_rec = calcular_perceptual_hash(datos_reciclada)
        sha_rec = calcular_sha256(datos_reciclada)

        es_dup, dup_id, dist = buscar_foto_reciclada(
            self.db,
            hash_perceptual=h_rec,
            sha256_actual=sha_rec,
            evidencia_id_actual=202,
        )

        self.assertTrue(es_dup)
        self.assertEqual(dup_id, 101)
        self.assertIsNotNone(dist)
        self.assertLessEqual(dist, 5)


if __name__ == "__main__":
    unittest.main()
