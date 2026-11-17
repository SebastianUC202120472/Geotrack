# Mensajes de voz: tamano y formato real validados, limites, idioma detectado; el audio no se guarda.
import httpx

from app.core.config import settings
from app.main import app

WEBM = b"\x1a\x45\xdf\xa3" + b"\x00" * 200


def _subir(cliente, cabecera, contenido: bytes):
    """Sube un audio al endpoint de voz. Recibe cliente, cabecera y bytes."""
    return cliente.post("/api/atencion/voz", headers=cabecera, files={"audio": ("audio.webm", contenido, "audio/webm")})


def _whisper(texto: str, idioma: str = "spanish", duracion: float = 3.0):
    """Cliente http que simula Whisper de Groq. Recibe el texto, el idioma y la duracion."""
    recibido = {}

    def manejador(request: httpx.Request):
        recibido["url"] = str(request.url)
        recibido["cuerpo"] = request.content
        return httpx.Response(200, json={"text": texto, "language": idioma, "duration": duracion})

    return httpx.AsyncClient(transport=httpx.MockTransport(manejador)), recibido


def test_transcribe_y_detecta_el_idioma(cliente, abrir, monkeypatch):
    """Un audio valido se transcribe con Whisper, sin fijar el idioma, y se devuelve el idioma detectado."""
    monkeypatch.setattr(settings, "ATENCION_GROQ_API_KEY", "k")
    app.state.http_ia, recibido = _whisper(" where is my order? ", "english")
    r = _subir(cliente, abrir(), WEBM)
    assert r.status_code == 200 and r.json() == {"texto": "where is my order?", "idioma": "en"}
    assert recibido["url"].endswith("/audio/transcriptions")
    assert b'name="language"' not in recibido["cuerpo"]


def test_rechaza_lo_que_no_es_audio_o_es_muy_grande(cliente, abrir, monkeypatch):
    """Un archivo que no es audio (por su contenido real) o que supera el maximo se rechaza."""
    monkeypatch.setattr(settings, "ATENCION_GROQ_API_KEY", "k")
    app.state.http_ia, _ = _whisper("x")
    cabecera = abrir()
    assert _subir(cliente, cabecera, b"<script>alert(1)</script>" * 5).status_code == 400
    assert _subir(cliente, cabecera, WEBM + b"\x00" * (settings.ATENCION_VOZ_MAX_KB * 1024)).status_code == 400


def test_rechaza_audio_mas_largo_que_el_maximo(cliente, abrir, monkeypatch):
    """Si Whisper informa una duracion mayor al maximo, el texto no se usa."""
    monkeypatch.setattr(settings, "ATENCION_GROQ_API_KEY", "k")
    app.state.http_ia, _ = _whisper("hola", duracion=settings.ATENCION_VOZ_MAX_SEG + 30)
    assert _subir(cliente, abrir(), WEBM).status_code == 400


def test_limite_de_audios_por_conversacion(cliente, abrir, monkeypatch):
    """Una conversacion no puede enviar audios sin fin."""
    monkeypatch.setattr(settings, "ATENCION_GROQ_API_KEY", "k")
    monkeypatch.setattr(settings, "ATENCION_AUDIOS_POR_CONVERSACION", 1)
    app.state.http_ia, _ = _whisper("hola")
    cabecera = abrir()
    assert _subir(cliente, cabecera, WEBM).status_code == 200
    assert _subir(cliente, cabecera, WEBM).status_code == 429


def test_sin_clave_de_groq_el_widget_usa_el_dictado_del_navegador(cliente, abrir, monkeypatch):
    """Sin clave, el estado avisa que no hay voz en el servidor y el endpoint responde 503."""
    monkeypatch.setattr(settings, "ATENCION_GROQ_API_KEY", "")
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")
    assert cliente.get("/api/atencion/estado").json()["voz_servidor"] is False
    assert _subir(cliente, abrir(), WEBM).status_code == 503


def test_voz_exige_token_de_conversacion(cliente):
    """Sin conversacion no se puede usar la transcripcion (cuesta cuota)."""
    r = cliente.post("/api/atencion/voz", headers={"Origin": "http://sitio.test"},
                     files={"audio": ("a.webm", WEBM, "audio/webm")})
    assert r.status_code == 401
