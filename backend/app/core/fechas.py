# Utilidades de fecha para la zona horaria de la operacion.
# Las marcas de tiempo se guardan en UTC (datetime.utcnow), pero "el dia" que ve el
# cliente corporativo o el landing es el dia LOCAL. Sin esto, para una operacion
# peruana (UTC-5) el dia cambiaria a las 7 p.m. hora de Lima.
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.core.config import settings


def zona() -> timezone | ZoneInfo:
    """Devuelve la zona horaria configurada; cae a UTC si el sistema no la conoce. Sin input."""
    try:
        return ZoneInfo(settings.ZONA_HORARIA)
    except (ZoneInfoNotFoundError, ValueError):
        return timezone.utc


def hoy_local() -> datetime.date:
    """Fecha de hoy en la zona de la operacion. Sin input."""
    return datetime.now(zona()).date()


def rango_utc_del_dia(dia=None) -> tuple[datetime, datetime]:
    """Devuelve (inicio, fin) en UTC *naive* del dia local indicado. Recibe la fecha (por
    defecto hoy). Se compara contra columnas guardadas con utcnow(), que son naive."""
    dia = dia or hoy_local()
    tz = zona()
    inicio = datetime.combine(dia, time.min, tzinfo=tz).astimezone(timezone.utc)
    fin = datetime.combine(dia, time.max, tzinfo=tz).astimezone(timezone.utc)
    return inicio.replace(tzinfo=None), fin.replace(tzinfo=None)


def fecha_local_de(momento: datetime):
    """Convierte una marca UTC naive a la fecha local. Recibe el datetime (o None)."""
    if momento is None:
        return None
    if momento.tzinfo is None:
        momento = momento.replace(tzinfo=timezone.utc)
    return momento.astimezone(zona()).date()


def es_hoy_local(momento: datetime) -> bool:
    """Dice si una marca UTC naive cae en el dia local de hoy. Recibe el datetime."""
    fecha = fecha_local_de(momento)
    return fecha is not None and fecha == hoy_local()


# timedelta se reexporta por comodidad de los llamadores que calculan ventanas.
__all__ = ["zona", "hoy_local", "rango_utc_del_dia", "fecha_local_de", "es_hoy_local", "timedelta"]
