# Mensajes de voz: tamaño y formato real validados; el audio no se guarda.
import httpx

from app.core.config import settings
from app.main import app
from tests.conftest import cabecera

WEBM = b"\x1a\x45\xdf\xa3" + b"\x00" * 200


def _enviar(cliente, contenido: bytes, nombre="audio.webm", tipo="audio/webm"):
    """Sube un audio al endpoint de voz. Recibe cliente y bytes."""
    return cliente.post("/api/asistente/voz", files={"audio": (nombre, contenido, tipo)}, headers=cabecera())


def test_rechaza_archivo_que_no_es_audio(cliente, monkeypatch):
    """Un archivo con extension de audio pero contenido de otro tipo se rechaza."""
    monkeypatch.setattr(settings, "GROQ_API_KEY", "k")
    r = _enviar(cliente, b"<script>alert(1)</script>" * 5)
    assert r.status_code == 400


def test_rechaza_audio_demasiado_grande(cliente, monkeypatch):
    """Un audio que supera el tamaño maximo se rechaza."""
    monkeypatch.setattr(settings, "GROQ_API_KEY", "k")
    r = _enviar(cliente, WEBM + b"\x00" * (settings.ASISTENTE_VOZ_MAX_KB * 1024))
    assert r.status_code == 400


def test_transcribe_y_devuelve_texto(cliente, monkeypatch):
    """Un audio valido se transcribe y se devuelve el texto entendido."""
    monkeypatch.setattr(settings, "GROQ_API_KEY", "k")
    recibido = {}

    def whisper(request: httpx.Request):
        recibido["url"] = str(request.url)
        return httpx.Response(200, json={"text": " ¿Dónde está Juan ahorita? ", "duration": 3.2})

    app.state.http_ia = httpx.AsyncClient(transport=httpx.MockTransport(whisper))
    r = _enviar(cliente, WEBM)
    assert r.status_code == 200 and r.json() == {"texto": "¿Dónde está Juan ahorita?"}
    assert recibido["url"].endswith("/audio/transcriptions")


def test_rechaza_audio_demasiado_largo(cliente, monkeypatch):
    """Si la transcripcion indica que el audio dura mas del maximo, se rechaza."""
    monkeypatch.setattr(settings, "GROQ_API_KEY", "k")
    app.state.http_ia = httpx.AsyncClient(transport=httpx.MockTransport(
        lambda r: httpx.Response(200, json={"text": "hola", "duration": 600})
    ))
    assert _enviar(cliente, WEBM).status_code == 400


def test_sin_clave_avisa_que_no_hay_voz_en_servidor(cliente, monkeypatch):
    """Sin clave de Groq el endpoint responde 503 y el widget usa el dictado del navegador."""
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")
    assert cliente.get("/api/asistente/estado").json()["voz_servidor"] is False
    assert _enviar(cliente, WEBM).status_code == 503
