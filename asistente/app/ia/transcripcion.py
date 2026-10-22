# Transcripcion de mensajes de voz con Whisper (API de Groq, compatible con OpenAI).
# El audio se procesa en memoria y se descarta al terminar: nunca se escribe a disco
# ni se guarda en la base de datos.
import httpx

from app.core.config import settings


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


def validar_audio(contenido: bytes) -> tuple[str, str]:
    """Aplica los topes de tamaño y formato antes de transcribir. Recibe los bytes del audio."""
    if not contenido:
        raise ErrorAudio("El audio está vacío")
    if len(contenido) > settings.ASISTENTE_VOZ_MAX_KB * 1024:
        raise ErrorAudio(f"El audio supera el máximo de {settings.ASISTENTE_VOZ_MAX_KB} KB")
    return detectar_formato(contenido)


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
            async with httpx.AsyncClient(timeout=settings.ASISTENTE_IA_TIMEOUT_SEG) as cliente:
                r = await cliente.post(url, data=datos, files=archivos, headers=cabeceras)
    except httpx.HTTPError as exc:
        raise ErrorTranscripcion("No se pudo conectar con el servicio de transcripción") from exc
    if r.status_code != 200:
        raise ErrorTranscripcion(f"El servicio de transcripción respondió {r.status_code}")
    try:
        cuerpo = r.json()
    except ValueError as exc:
        raise ErrorTranscripcion("Respuesta inválida del servicio de transcripción") from exc
    duracion = float(cuerpo.get("duration") or 0)
    if duracion > settings.ASISTENTE_VOZ_MAX_SEG + 2:
        raise ErrorAudio(f"El audio dura más de {settings.ASISTENTE_VOZ_MAX_SEG} segundos")
    return (cuerpo.get("text") or "").strip()
