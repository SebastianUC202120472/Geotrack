# Fechas en la zona horaria de la operacion. El nucleo guarda las marcas en UTC
# "naive" (sin zona), asi que hay que convertirlas antes de hablar de "hoy".
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.core.config import settings

_DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


def zona():
    """Devuelve la zona horaria configurada (UTC si no existe). Sin input."""
    try:
        return ZoneInfo(settings.ZONA_HORARIA)
    except (ZoneInfoNotFoundError, ValueError):
        return timezone.utc


def ahora_utc() -> datetime:
    """Fecha y hora actual en UTC sin zona (mismo formato que guarda el nucleo). Sin input."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def ahora_local() -> datetime:
    """Fecha y hora actual en la zona de la operacion. Sin input."""
    return datetime.now(zona())


def hoy_local() -> date:
    """Fecha de hoy en la zona de la operacion. Sin input."""
    return ahora_local().date()


def leer_fecha_core(valor) -> datetime | None:
    """Convierte una fecha del nucleo (texto ISO en UTC) a hora local. Recibe el valor crudo."""
    if not valor:
        return None
    try:
        momento = datetime.fromisoformat(str(valor).replace("Z", "+00:00"))
    except ValueError:
        return None
    if momento.tzinfo is None:
        momento = momento.replace(tzinfo=timezone.utc)
    return momento.astimezone(zona())


def fecha_local_core(valor) -> date | None:
    """Fecha local (sin hora) de una marca del nucleo. Recibe el valor crudo."""
    momento = leer_fecha_core(valor)
    return momento.date() if momento else None


def texto_fecha_hora(valor) -> str | None:
    """Formatea una marca del nucleo como 'dd/mm/aaaa hh:mm' en hora local. Recibe el valor crudo."""
    momento = leer_fecha_core(valor)
    return momento.strftime("%d/%m/%Y %H:%M") if momento else None


def descripcion_hoy() -> str:
    """Texto con el dia y la hora actual para el modelo, ej. 'jueves 22/10/2026, 10:15'. Sin input."""
    ahora = ahora_local()
    return f"{_DIAS[ahora.weekday()]} {ahora.strftime('%d/%m/%Y')}, {ahora.strftime('%H:%M')}"
