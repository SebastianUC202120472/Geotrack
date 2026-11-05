# Enlaces firmados para vincular un chat de Telegram a un pedido o a un conductor.
# El enlace del pedido solo lo entrega el portal despues de verificar codigo + DNI, y el del
# conductor solo el administrador: el token va firmado con HMAC y vence, asi que nadie puede
# suscribirse a un pedido ajeno escribiendo "/start" con un codigo inventado o correlativo.
# Formato (cabe en el parametro start de Telegram: maximo 64 caracteres [A-Za-z0-9_-]):
#   P<id>_<exp>_<firma>  (pedido)   ·   C<id>_<exp>_<firma>  (conductor)
import base64
import hashlib
import hmac
import re
import time

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories import pedido_repository

VIGENCIA_SEG = 24 * 3600
_LETRAS = {"pedido": "P", "conductor": "C"}
_TIPOS = {v: k for k, v in _LETRAS.items()}
_PATRON = re.compile(r"^([PC])(\d{1,9})_(\d{10})_([A-Za-z0-9_-]{16})$")


def _firma(letra: str, entidad_id: int, exp: int) -> str:
    """Firma HMAC-SHA256 recortada del vinculo. Recibe la letra del tipo, el id y el vencimiento."""
    mac = hmac.new(settings.SECRET_KEY.encode(), f"vinculo|{letra}|{entidad_id}|{exp}".encode(), hashlib.sha256)
    return base64.urlsafe_b64encode(mac.digest()[:12]).decode()


def crear_token(entidad_tipo: str, entidad_id: int, ahora: float | None = None) -> str:
    """Token firmado que vence en 24 h. Recibe el tipo ("pedido" o "conductor") y el id."""
    letra = _LETRAS[entidad_tipo]
    exp = int(ahora if ahora is not None else time.time()) + VIGENCIA_SEG
    return f"{letra}{int(entidad_id)}_{exp}_{_firma(letra, int(entidad_id), exp)}"


def leer_token(token: str, ahora: float | None = None) -> tuple[str, int] | None:
    """Devuelve (tipo, id) si el token es autentico y no vencio; None si no. Recibe el token."""
    m = _PATRON.match((token or "").strip())
    if not m:
        return None
    letra, entidad_id, exp = m.group(1), int(m.group(2)), int(m.group(3))
    if exp < int(ahora if ahora is not None else time.time()):
        return None
    if not hmac.compare_digest(_firma(letra, entidad_id, exp), m.group(4)):
        return None
    return _TIPOS[letra], entidad_id


def enlace_telegram(entidad_tipo: str, entidad_id: int) -> str | None:
    """Enlace t.me del bot con el token, o None si Telegram no esta configurado. Recibe tipo e id."""
    usuario = (settings.TELEGRAM_BOT_USERNAME or "").strip().lstrip("@")
    if not (settings.NOTIFICACIONES_HABILITADAS and usuario and settings.TELEGRAM_BOT_TOKEN):
        return None
    return f"https://t.me/{usuario}?start={crear_token(entidad_tipo, entidad_id)}"


def enlace_pedido(db: Session, codigo: str) -> dict:
    """Enlace de avisos del pedido ya verificado en el portal. Recibe el codigo normalizado."""
    pedido = pedido_repository.obtener_por_codigo(db, codigo)
    if pedido is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pedido no encontrado")
    url = enlace_telegram("pedido", pedido.id)
    return {"disponible": url is not None, "canal": "telegram", "url": url}
