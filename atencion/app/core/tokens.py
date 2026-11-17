# Token de conversacion anonima.
# El visitante no tiene cuenta: al aceptar el aviso de privacidad recibe un token firmado
# (HMAC-SHA256) que lo ata a SU conversacion y vence solo. Formato: id.vence.firma.
# Sin el secreto nadie puede fabricar un token para leer o escribir otra conversacion.
import hashlib
import hmac
import re
import secrets
import time

from app.core.config import settings
from app.core.registro import log

_RE_TOKEN = re.compile(r"^([a-f0-9]{32})\.(\d{10})\.([a-f0-9]{64})$")


def _cargar_secreto() -> bytes:
    """Secreto de firma: el del .env o uno aleatorio por arranque (con aviso en el log). Sin input."""
    if settings.ATENCION_SECRETO_CONVERSACION:
        return settings.ATENCION_SECRETO_CONVERSACION.encode()
    log.warning("ATENCION_SECRETO_CONVERSACION vacío: se usa uno temporal; las conversaciones se pierden al reiniciar")
    return secrets.token_bytes(32)


SECRETO = _cargar_secreto()


def _firmar(conversacion_id: str, vence: int) -> str:
    """Firma el id y el vencimiento. Recibe ambos."""
    return hmac.new(SECRETO, f"{conversacion_id}.{vence}".encode(), hashlib.sha256).hexdigest()


def emitir(conversacion_id: str, ahora: float | None = None) -> str:
    """Emite el token de una conversacion nueva. Recibe el id (32 hex) y el momento (pruebas)."""
    vence = int((ahora or time.time()) + settings.ATENCION_CONVERSACION_VENCE_MIN * 60)
    return f"{conversacion_id}.{vence}.{_firmar(conversacion_id, vence)}"


def validar(token: str | None, ahora: float | None = None) -> str | None:
    """Devuelve el id de la conversacion si el token es autentico y vigente; si no, None. Recibe el token."""
    coincide = _RE_TOKEN.match((token or "").strip())
    if not coincide:
        return None
    conversacion_id, vence, firma = coincide.group(1), int(coincide.group(2)), coincide.group(3)
    if not hmac.compare_digest(firma, _firmar(conversacion_id, vence)):
        return None
    if vence < (ahora or time.time()):
        return None
    return conversacion_id
