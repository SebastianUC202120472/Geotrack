# Transcripcion de mensajes de voz con Whisper (API de Groq, compatible con OpenAI).
# El audio se procesa en memoria y se descarta al terminar: nunca se escribe a disco
# ni se guarda en la base de datos.
import io
import wave

import httpx

from app.core.config import settings
from app.ia.proveedores import timeout_http_ia


class ErrorAudio(ValueError):
    """El audio no cumple los limites o no tiene un formato admitido."""


class ErrorTranscripcion(Exception):
    """El servicio de transcripcion fallo o no esta configurado."""


# Firmas (bytes iniciales) de los formatos que graba un navegador. Se valida el tipo
# REAL del archivo, no la extension ni el Content-Type que manda el cliente.
_FORMATOS = (
    ("webm", "audio/webm", lambda b: b[:4] == b"\x1a\x45\xdf\xa3"),
    ("ogg", "audio/ogg", lambda b: b[:4] == b"OggS"),
    ("wav", "audio/wav", lambda b: b[:4] == b"RIFF" and b[8:12] == b"WAVE"),
    ("m4a", "audio/mp4", lambda b: b[4:8] == b"ftyp"),
    ("mp3", "audio/mpeg", lambda b: b[:3] == b"ID3" or (len(b) > 1 and b[0] == 0xFF and (b[1] & 0xE0) == 0xE0)),
)


def detectar_formato(contenido: bytes) -> tuple[str, str]:
    """Detecta el formato real del audio por su firma. Recibe los bytes; devuelve (extension, tipo)."""
    for extension, tipo, coincide in _FORMATOS:
        if len(contenido) >= 12 and coincide(contenido):
            return extension, tipo
    raise ErrorAudio("Formato de audio no admitido")


def _duracion_wav(contenido: bytes) -> float | None:
    """Duracion de un WAV leida de su cabecera, o None si no se puede leer. Recibe los bytes."""
    try:
        with wave.open(io.BytesIO(contenido)) as w:
            return w.getnframes() / float(w.getframerate())
    except (wave.Error, EOFError, ZeroDivisionError):
        return None


def _validar_duracion(segundos: float) -> None:
    """Corta los audios que duran mas del maximo (con 2 s de tolerancia). Recibe la duracion."""
    if segundos > settings.ASISTENTE_VOZ_MAX_SEG + 2:
        raise ErrorAudio(f"El audio dura más de {settings.ASISTENTE_VOZ_MAX_SEG} segundos")


def validar_audio(contenido: bytes) -> tuple[str, str]:
    """Aplica los topes de tamaño, formato y (en WAV) duración antes de transcribir. Recibe los bytes.
    En WAV la duración se lee de la cabecera, así un audio largo se rechaza sin enviarlo al proveedor;
    en los formatos comprimidos se controla con la duración que devuelve la transcripción."""
    if not contenido:
        raise ErrorAudio("El audio está vacío")
    if len(contenido) > settings.ASISTENTE_VOZ_MAX_KB * 1024:
        raise ErrorAudio(f"El audio supera el máximo de {settings.ASISTENTE_VOZ_MAX_KB} KB")
    extension, tipo = detectar_formato(contenido)
    if extension == "wav":
        duracion = _duracion_wav(contenido)
        if duracion is not None:
            _validar_duracion(duracion)
    return extension, tipo


def voz_en_servidor_disponible() -> bool:
    """Dice si hay una clave para transcribir en el servidor. Sin input."""
    return bool(settings.GROQ_API_KEY)


async def transcribir(contenido: bytes, http: httpx.AsyncClient | None = None) -> str:
    """Transcribe un audio validado y devuelve el texto. Recibe los bytes y un cliente http opcional."""
    if not voz_en_servidor_disponible():
        raise ErrorTranscripcion("La transcripción en el servidor no está configurada")
    extension, tipo = validar_audio(contenido)
    archivos = {"file": (f"mensaje.{extension}", contenido, tipo)}
    datos = {
        "model": settings.ASISTENTE_VOZ_MODELO,
        "language": "es",
        "response_format": "verbose_json",
        "temperature": "0",
    }
    url = settings.GROQ_URL.rstrip("/") + "/audio/transcriptions"
    cabeceras = {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}
    try:
        if http is not None:
            r = await http.post(url, data=datos, files=archivos, headers=cabeceras)
        else:
            async with httpx.AsyncClient(timeout=timeout_http_ia()) as cliente:
                r = await cliente.post(url, data=datos, files=archivos, headers=cabeceras)
    except httpx.HTTPError as exc:
        raise ErrorTranscripcion("No se pudo conectar con el servicio de transcripción") from exc
    if r.status_code != 200:
        raise ErrorTranscripcion(f"El servicio de transcripción respondió {r.status_code}")
    try:
        cuerpo = r.json()
    except ValueError as exc:
        raise ErrorTranscripcion("Respuesta inválida del servicio de transcripción") from exc
    _validar_duracion(float(cuerpo.get("duration") or 0))
    return (cuerpo.get("text") or "").strip()
