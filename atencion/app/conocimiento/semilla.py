# Carga el borrador de la base de conocimiento (semilla.json) y el aviso de privacidad.
# La semilla solo se inserta si las tablas estan vacias: despues manda lo que se edite
# desde la pantalla de administracion.
import json
from functools import lru_cache
from pathlib import Path

_CARPETA = Path(__file__).parent
_CAMPOS_IDIOMA = ("titulo", "contenido")


def _leer(nombre: str) -> dict:
    """Lee un JSON de esta carpeta. Recibe el nombre del archivo."""
    with open(_CARPETA / nombre, encoding="utf-8") as archivo:
        return json.load(archivo)


def articulos_semilla() -> list[dict]:
    """Articulos de la semilla en filas por idioma, validados. Sin input."""
    filas = []
    claves = set()
    for item in _leer("semilla.json")["articulos"]:
        clave = item["clave"]
        if clave in claves:
            raise ValueError(f"Clave repetida en la semilla: {clave}")
        claves.add(clave)
        for idioma in ("es", "en"):
            texto = item[idioma]
            if not all(str(texto.get(c, "")).strip() for c in _CAMPOS_IDIOMA):
                raise ValueError(f"Falta titulo o contenido en {clave}/{idioma}")
            filas.append({
                "clave": clave, "idioma": idioma, "categoria": item.get("categoria", "general"),
                "titulo": texto["titulo"].strip(), "contenido": texto["contenido"].strip(),
                "etiquetas": item.get("etiquetas", "").strip(),
            })
    return filas


@lru_cache(maxsize=1)
def aviso_privacidad() -> dict:
    """Aviso de privacidad (Ley 29733) en espanol e ingles, con su version. Sin input."""
    return _leer("aviso_privacidad.json")
