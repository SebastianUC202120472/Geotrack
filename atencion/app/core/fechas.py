# Fechas en hora de Lima. La base guarda UTC sin zona; los topes diarios empiezan a la
# medianoche de Lima.
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from app.core.config import settings


def ahora_utc() -> datetime:
    """Momento actual en UTC sin zona (como se guarda en la base). Sin input."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def ahora_local() -> datetime:
    """Momento actual en la zona horaria configurada (Lima). Sin input."""
    return datetime.now(ZoneInfo(settings.ZONA_HORARIA))


def inicio_del_dia_utc() -> datetime:
    """Medianoche de hoy (hora de Lima) expresada en UTC sin zona. Sin input."""
    medianoche = ahora_local().replace(hour=0, minute=0, second=0, microsecond=0)
    return medianoche.astimezone(timezone.utc).replace(tzinfo=None)
