# Entorno de pruebas del asistente de atencion: SQLite temporal y un proveedor de IA falso con
# respuestas guionadas. No se llama a ningun servicio real ni se usan datos reales.
import copy
import json
import os
import tempfile

_tmp = tempfile.mkdtemp(prefix="atencion_test_")
os.environ["ATENCION_ENABLED"] = "true"
os.environ["ATENCION_DATABASE_URL"] = f"sqlite:///{os.path.join(_tmp, 'atencion.db')}"
os.environ["ATENCION_DB_SCHEMA"] = ""
os.environ["ATENCION_CORS_ORIGINS"] = "http://sitio.test"
os.environ["ATENCION_SECRETO_CONVERSACION"] = "secreto-solo-para-pruebas-0123456789"
os.environ["ATENCION_SEG_MINIMOS_PRIMER_MENSAJE"] = "0"
os.environ["ATENCION_PROVEEDORES"] = "gemini"
os.environ["ATENCION_GEMINI_API_KEY"] = "clave-de-prueba"

import httpx  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.api.deps import limpiar_cache_admin  # noqa: E402
from app.conocimiento.semilla import aviso_privacidad  # noqa: E402
from app.core.limites import limitador  # noqa: E402
from app.db.database import Base, engine  # noqa: E402
from app.main import app, preparar_conocimiento  # noqa: E402
from app.services.sesion import sesiones  # noqa: E402
from scripts.portal_simulado import PortalFalso  # noqa: E402,F401  (fixture "portal")

ORIGEN = {"Origin": "http://sitio.test"}


class CadenaFalsa:
    """Proveedor de IA guionado: cada ronda devuelve textos y/o llamadas a funciones."""

    def __init__(self, rondas: list[dict] | None = None, error: Exception | None = None):
        self.rondas = list(rondas or [])
        self.error = error
        self.recibido: list[tuple[list, list]] = []
        self.proveedores = ["falso"]

    async def transmitir(self, mensajes, herramientas, http):
        """Devuelve la siguiente ronda guionada y guarda lo que recibio. Recibe mensajes, herramientas y http."""
        self.recibido.append((copy.deepcopy(mensajes), herramientas))
        if self.error:
            raise self.error
        ronda = self.rondas.pop(0) if self.rondas else {"texto": ["(sin guion)"]}
        yield "proveedor", "falso"
        for fragmento in ronda.get("texto", []):
            yield "texto", fragmento
        yield "llamadas", ronda.get("llamadas", [])


def llamada(nombre: str, argumentos: dict, ident: str = "c1") -> dict:
    """Arma una llamada a funcion como la devolveria el modelo. Recibe nombre y argumentos."""
    return {"id": ident, "type": "function", "function": {"name": nombre, "arguments": json.dumps(argumentos)}}


def eventos_sse(texto: str) -> list[dict]:
    """Convierte el cuerpo Server-Sent Events en una lista de eventos. Recibe el texto."""
    return [json.loads(b[len("data: "):]) for b in texto.split("\n\n") if b.startswith("data: ")]


def texto_de(eventos: list[dict]) -> str:
    """Une el texto visible de una respuesta (aplicando un 'reemplazar' si llego). Recibe los eventos."""
    texto = ""
    for e in eventos:
        if e["tipo"] == "texto":
            texto += e["texto"]
        elif e["tipo"] == "reemplazar":
            texto = e["texto"]
    return texto


@pytest.fixture()
def portal():
    """Portal simulado nuevo para cada prueba."""
    return PortalFalso()


@pytest.fixture()
def cliente(portal):
    """Cliente de pruebas con BD limpia, base de conocimiento semilla, portal simulado y limites reiniciados."""
    Base.metadata.drop_all(bind=engine)
    preparar_conocimiento()
    limitador.limpiar()
    sesiones.limpiar()
    limpiar_cache_admin()
    with TestClient(app) as c:
        app.state.http_core = httpx.AsyncClient(transport=httpx.MockTransport(portal))
        yield c


@pytest.fixture()
def abrir(cliente):
    """Funcion que abre una conversacion y devuelve la cabecera con su token. Recibe idioma opcional."""
    def _abrir(idioma: str = "es") -> dict:
        r = cliente.post("/api/atencion/conversaciones", headers=ORIGEN, json={
            "acepta_privacidad": True, "version_aviso": aviso_privacidad()["version"], "idioma": idioma,
        })
        assert r.status_code == 201, r.text
        return {**ORIGEN, "X-Conversacion": r.json()["token"]}
    return _abrir


def enviar(cliente, cabecera: dict, mensaje: str, cadena: CadenaFalsa | None = None):
    """Envia un mensaje con una cadena de IA falsa y devuelve (respuesta, eventos). Recibe cliente, cabecera,
    mensaje y la cadena (opcional)."""
    if cadena is not None:
        app.state.cadena = cadena
    r = cliente.post("/api/atencion/chat", headers=cabecera, json={"mensaje": mensaje})
    return r, (eventos_sse(r.text) if r.status_code == 200 else [])
