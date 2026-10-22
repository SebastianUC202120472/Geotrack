# Dependencias comunes de los endpoints del asistente.
# La identidad del usuario NO se decodifica aqui: se pregunta al nucleo (/usuarios/yo)
# con el mismo token. Asi el asistente respeta la desactivacion de cuentas y los roles
# del nucleo sin conocer su clave secreta.
import hashlib
import time
from collections import OrderedDict

from fastapi import HTTPException, Request, status

from app.core.config import settings
from app.herramientas.cliente_core import ClienteCore, ErrorCore, SesionInvalida, SinPermiso

ROLES_PANEL = ("admin", "almacen")
_TTL_SEG = 60
_MAX_CACHE = 500
_cache: OrderedDict[str, tuple[float, dict]] = OrderedDict()


def exigir_activo() -> None:
    """Corta la peticion si el modulo esta apagado por variable de entorno. Sin input."""
    if not settings.ASISTENTE_ENABLED:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="El asistente está desactivado")


def leer_token(request: Request) -> str:
    """Extrae el token Bearer de la cabecera Authorization. Recibe la peticion."""
    cabecera = request.headers.get("authorization", "")
    tipo, _, token = cabecera.partition(" ")
    if tipo.lower() != "bearer" or not token.strip() or len(token) > 4096:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Falta iniciar sesión")
    return token.strip()


def limpiar_cache() -> None:
    """Vacia la cache de identidades (para pruebas). Sin input."""
    _cache.clear()


async def obtener_usuario(request: Request) -> dict:
    """Valida el token contra el nucleo y devuelve {id, correo, rol, nombre, token}. Recibe la peticion."""
    exigir_activo()
    token = leer_token(request)
    llave = hashlib.sha256(token.encode()).hexdigest()
    ahora = time.monotonic()
    guardado = _cache.get(llave)
    if guardado and guardado[0] > ahora:
        return guardado[1]

    http = getattr(request.app.state, "http_core", None)
    try:
        perfil = await ClienteCore(token, http).get("/usuarios/yo")
    except SesionInvalida:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Tu sesión expiró")
    except SinPermiso:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="El asistente es solo para el panel")
    except ErrorCore:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="No se pudo validar la sesión")

    if perfil.get("rol") not in ROLES_PANEL or not perfil.get("estado", True):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="El asistente es solo para el panel")
    usuario = {
        "id": int(perfil["id"]),
        "correo": perfil.get("correo", ""),
        "rol": perfil["rol"],
        "nombre": perfil.get("nombre") or "",
        "token": token,
    }
    _cache[llave] = (ahora + _TTL_SEG, usuario)
    if len(_cache) > _MAX_CACHE:
        _cache.popitem(last=False)
    return usuario
