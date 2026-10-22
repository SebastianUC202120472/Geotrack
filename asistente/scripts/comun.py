# Utilidades compartidas por los scripts de la demo: leer las credenciales del admin del
# .env e iniciar sesion por la API. Solo usa la libreria estandar (corre en cualquier PC
# con Python 3.9+ sin instalar nada). Nunca imprime la contrasena ni el token.
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

RAIZ_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
URL_BASE_POR_DEFECTO = "http://localhost:8080"
CLAVES_PERMITIDAS = ("ADMIN_EMAIL", "ADMIN_PASSWORD")


def preparar_consola() -> None:
    """Fuerza UTF-8 en la consola para que las tildes salgan bien en Windows. Sin input."""
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass


def leer_credenciales(ruta_env: str | None = None) -> tuple[str, str]:
    """Lee SOLO ADMIN_EMAIL y ADMIN_PASSWORD del .env (el resto se ignora). Recibe la ruta opcional.
    Devuelve (correo, clave). Termina con un mensaje claro si falta el archivo o alguna clave."""
    ruta = ruta_env or os.path.join(RAIZ_REPO, ".env")
    if not os.path.isfile(ruta):
        raise SystemExit(f"ERROR: no se encontró el archivo .env en {ruta}")
    valores = {}
    with open(ruta, encoding="utf-8-sig") as archivo:
        for linea in archivo:
            linea = linea.strip()
            if not linea or linea.startswith("#") or "=" not in linea:
                continue
            clave, valor = linea.split("=", 1)
            clave = clave.strip()
            if clave.startswith("export "):
                clave = clave[len("export "):].strip()
            if clave not in CLAVES_PERMITIDAS:
                continue
            valor = valor.strip()
            if len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in "\"'":
                valor = valor[1:-1]
            valores[clave] = valor
    faltan = [c for c in CLAVES_PERMITIDAS if not valores.get(c)]
    if faltan:
        raise SystemExit(f"ERROR: el .env no define {', '.join(faltan)}")
    return valores["ADMIN_EMAIL"], valores["ADMIN_PASSWORD"]


def _detalle_error(exc: urllib.error.HTTPError) -> str:
    """Extrae el 'detail' de una respuesta de error de FastAPI. Recibe la excepcion."""
    try:
        cuerpo = json.loads(exc.read().decode("utf-8") or "{}")
    except (ValueError, UnicodeDecodeError):
        return exc.reason or "sin detalle"
    detalle = cuerpo.get("detail", cuerpo) if isinstance(cuerpo, dict) else cuerpo
    if isinstance(detalle, list):  # errores de validacion (422)
        return "; ".join(f"{'.'.join(map(str, d.get('loc', [])))}: {d.get('msg')}" for d in detalle if isinstance(d, dict))
    return str(detalle)


class ErrorApi(Exception):
    """Respuesta HTTP con error. Guarda el codigo y el detalle legible."""

    def __init__(self, codigo: int, detalle: str):
        super().__init__(f"HTTP {codigo}: {detalle}")
        self.codigo = codigo
        self.detalle = detalle


def peticion(metodo: str, url: str, token: str | None = None, datos=None, formulario: dict | None = None,
             timeout: float = 30):
    """Hace una peticion y devuelve el JSON de respuesta. Recibe metodo, url, token y cuerpo
    (JSON en 'datos' o urlencoded en 'formulario'). Lanza ErrorApi si el servidor responde con error."""
    cabeceras = {"Accept": "application/json"}
    cuerpo = None
    if formulario is not None:
        cuerpo = urllib.parse.urlencode(formulario).encode("utf-8")
        cabeceras["Content-Type"] = "application/x-www-form-urlencoded"
    elif datos is not None:
        cuerpo = json.dumps(datos).encode("utf-8")
        cabeceras["Content-Type"] = "application/json"
    if token:
        cabeceras["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=cuerpo, headers=cabeceras, method=metodo)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            texto = resp.read().decode("utf-8")
            return json.loads(texto) if texto else None
    except urllib.error.HTTPError as exc:
        raise ErrorApi(exc.code, _detalle_error(exc)) from None
    except urllib.error.URLError as exc:
        raise SystemExit(f"ERROR: no se pudo conectar con {url} ({exc.reason}). ¿Está levantado docker compose?")


def iniciar_sesion(url_base: str, ruta_env: str | None = None) -> str:
    """Inicia sesion como admin con las credenciales del .env. Recibe la URL base y la ruta del .env.
    Devuelve el token (no se imprime)."""
    correo, clave = leer_credenciales(ruta_env)
    try:
        respuesta = peticion("POST", f"{url_base}/api/auth/login", formulario={"username": correo, "password": clave})
    except ErrorApi as exc:
        if exc.codigo == 429:
            raise SystemExit("ERROR: demasiados intentos de login. Espera un minuto y vuelve a correr el script.")
        raise SystemExit(f"ERROR: no se pudo iniciar sesión como admin (HTTP {exc.codigo}: {exc.detalle}). "
                         "Revisa ADMIN_EMAIL y ADMIN_PASSWORD en el .env.")
    token = (respuesta or {}).get("access_token")
    if not token:
        raise SystemExit("ERROR: el login no devolvió un token.")
    print("Sesión iniciada como administrador.")
    return token
