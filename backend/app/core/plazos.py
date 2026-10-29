# Plazos en dias habiles (lunes a viernes sin feriados nacionales del Peru), para el
# Libro de Reclamaciones: la ley da 15 dias habiles para responder (C41-03).
from datetime import date, timedelta

# Feriados nacionales de fecha fija (mes, dia).
_FERIADOS_FIJOS = {
    (1, 1), (5, 1), (6, 7), (6, 29), (7, 23), (7, 28), (7, 29), (8, 6),
    (8, 30), (10, 8), (11, 1), (12, 8), (12, 9), (12, 25),
}

PLAZO_RECLAMO_DIAS_HABILES = 15


def _domingo_de_pascua(anio: int) -> date:
    """Domingo de Pascua (computo gregoriano anonimo). Recibe el anio."""
    a, b, c = anio % 19, anio // 100, anio % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7  # noqa: E741
    m = (a + 11 * h + 22 * l) // 451
    mes = (h + l - 7 * m + 114) // 31
    dia = ((h + l - 7 * m + 114) % 31) + 1
    return date(anio, mes, dia)


def es_feriado(dia: date) -> bool:
    """True si el dia es feriado nacional (fijo o Jueves/Viernes Santo). Recibe la fecha."""
    if (dia.month, dia.day) in _FERIADOS_FIJOS:
        return True
    pascua = _domingo_de_pascua(dia.year)
    return dia in (pascua - timedelta(days=3), pascua - timedelta(days=2))


def es_habil(dia: date) -> bool:
    """True si el dia es habil (lunes a viernes y no feriado). Recibe la fecha."""
    return dia.weekday() < 5 and not es_feriado(dia)


def sumar_dias_habiles(inicio: date, dias: int) -> date:
    """Fecha en que vence un plazo de `dias` habiles contados desde el dia siguiente a `inicio`.
    Recibe la fecha de inicio y la cantidad de dias habiles."""
    actual, contados = inicio, 0
    while contados < dias:
        actual += timedelta(days=1)
        if es_habil(actual):
            contados += 1
    return actual


def dias_habiles_entre(desde: date, hasta: date) -> int:
    """Dias habiles desde el dia siguiente a `desde` hasta `hasta` inclusive (negativo si `hasta`
    ya paso). Recibe las dos fechas."""
    if hasta == desde:
        return 0
    paso = 1 if hasta > desde else -1
    actual, total = desde, 0
    while actual != hasta:
        actual += timedelta(days=paso)
        if es_habil(actual):
            total += paso
    return total
