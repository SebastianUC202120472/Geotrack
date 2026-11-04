# Mensajes de voz: tamaño y formato real validados; el audio no se guarda.
import io
import wave

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


def _wav(segundos: float, hz: int = 8000) -> bytes:
    """WAV de silencio (8 bits, mono) con la duracion pedida. Recibe segundos y frecuencia."""
    salida = io.BytesIO()
    with wave.open(salida, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(1)
        w.setframerate(hz)
        w.writeframes(b"\x80" * int(segundos * hz))
    return salida.getvalue()


def test_wav_largo_se_rechaza_sin_enviarlo_al_proveedor(cliente, monkeypatch):
    """Un WAV liviano pero mas largo que el maximo se corta por su cabecera: no llega a Whisper."""
    monkeypatch.setattr(settings, "GROQ_API_KEY", "k")
    llamadas = []
    app.state.http_ia = httpx.AsyncClient(transport=httpx.MockTransport(
        lambda r: llamadas.append(r) or httpx.Response(200, json={"text": "hola", "duration": 1})
    ))
    contenido = _wav(settings.ASISTENTE_VOZ_MAX_SEG + 15)
    assert len(contenido) < settings.ASISTENTE_VOZ_MAX_KB * 1024
    r = _enviar(cliente, contenido, "mensaje.wav", "audio/wav")
    assert r.status_code == 400 and "segundos" in r.json()["detail"]
    assert llamadas == []


def test_wav_corto_si_se_transcribe(cliente, monkeypatch):
    """Un WAV dentro del limite pasa la validacion y se transcribe."""
    monkeypatch.setattr(settings, "GROQ_API_KEY", "k")
    app.state.http_ia = httpx.AsyncClient(transport=httpx.MockTransport(
        lambda r: httpx.Response(200, json={"text": "hola", "duration": 3})
    ))
    assert _enviar(cliente, _wav(3), "mensaje.wav", "audio/wav").status_code == 200


def test_sin_clave_avisa_que_no_hay_voz_en_servidor(cliente, monkeypatch):
    """Sin clave de Groq el endpoint responde 503 y el widget usa el dictado del navegador."""
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")
    assert cliente.get("/api/asistente/estado").json()["voz_servidor"] is False
    assert _enviar(cliente, WEBM).status_code == 503
