# Bloques que acompañan la respuesta en el widget: tablas, graficos y enlaces.
# Los arma SIEMPRE el servidor a partir de los datos reales de la consulta; el modelo
# solo pide el formato. Asi ningun numero de un grafico sale de la IA.
from urllib.parse import urlencode

MAX_FILAS_TABLA = 20
MAX_BARRAS_GRAFICO = 15


def tabla(titulo: str, columnas: list[str], filas: list[list]) -> dict:
    """Arma un bloque de tabla corta. Recibe titulo, columnas y filas."""
    filas_cortas = [[_celda(v) for v in fila] for fila in filas[:MAX_FILAS_TABLA]]
    return {
        "tipo": "tabla",
        "titulo": titulo[:100],
        "columnas": [str(c)[:40] for c in columnas],
        "filas": filas_cortas,
        "total": len(filas),
    }


def grafico(titulo: str, datos: list[tuple[str, float]], forma: str = "barras") -> dict:
    """Arma un bloque de grafico simple (barras o torta). Recibe titulo, pares (etiqueta, valor) y forma."""
    ordenados = sorted(datos, key=lambda par: par[1], reverse=True)[:MAX_BARRAS_GRAFICO]
    return {
        "tipo": "grafico",
        "titulo": titulo[:100],
        "forma": "torta" if forma == "torta" else "barras",
        "datos": [{"etiqueta": str(e or "Sin dato")[:40], "valor": round(float(v), 2)} for e, v in ordenados],
    }


def enlace(texto: str, ruta: str, params: dict | None = None) -> dict | None:
    """Arma un boton que abre una pantalla del panel con filtros. Recibe texto, ruta y filtros."""
    if not ruta.startswith("/panel"):
        return None
    limpios = {k: v for k, v in (params or {}).items() if v not in (None, "")}
    destino = ruta + (("?" + urlencode(limpios)) if limpios else "")
    return {"tipo": "enlace", "texto": texto[:60], "ruta": destino}


def _celda(valor):
    """Normaliza el valor de una celda (texto corto o numero). Recibe el valor."""
    if valor is None:
        return "—"
    if isinstance(valor, (int, float)):
        return valor
    return str(valor)[:80]
