import hashlib
import time
from collections import OrderedDict
import httpx
from fastapi import HTTPException, Request, status

from app.core.config import settings
from app.core.registro import obtener_logger

_log = obtener_logger("api.deps")

_TTL_SEG = 60.0
_MAX_CACHE = 500
_cache_identidad: OrderedDict[str, tuple[float, dict]] = OrderedDict()


def limpiar_cache_identidad() -> None:
    """Limpia la caché de sesiones validadas (para pruebas)."""
    _cache_identidad.clear()


def exigir_activo() -> None:
    """Rechaza la petición con 503 si el módulo de auditoría está apagado."""
    if not settings.AUDITORIA_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El módulo de auditoría de evidencias está desactivado",
        )


def leer_token_bearer(request: Request) -> str:
    """Extrae el token Bearer del header Authorization."""
    cabecera = request.headers.get("authorization", "")
    tipo, _, token = cabecera.partition(" ")
    if tipo.lower() != "bearer" or not token.strip() or len(token) > 4096:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Falta iniciar sesión",
        )
    return token.strip()


async def obtener_admin_actual(request: Request) -> dict:
    """Valida el token contra el núcleo (/usuarios/yo) y exige rol exclusivo 'admin'."""
    exigir_activo()
    token = leer_token_bearer(request)
    llave = hashlib.sha256(token.encode()).hexdigest()
    ahora = time.monotonic()

    guardado = _cache_identidad.get(llave)
    if guardado and guardado[0] > ahora:
        return guardado[1]

    url = f"{settings.CORE_API_URL.rstrip('/')}/usuarios/yo"
    cliente_inyectado = getattr(request.app.state, "http_core", None)
    cerrar = cliente_inyectado is None
    cliente = cliente_inyectado or httpx.AsyncClient(timeout=settings.CORE_TIMEOUT_SEG)

    try:
        resp = await cliente.get(url, headers={"Authorization": f"Bearer {token}"})
    except httpx.RequestError as exc:
        _log.warning("No se pudo contactar al núcleo para validar sesión: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudo validar la sesión con el núcleo",
        )
    finally:
        if cerrar:
            await cliente.aclose()

    if resp.status_code == 401:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Tu sesión expiró")
    if resp.status_code == 403:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado")
    if resp.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Error validando sesión con el núcleo",
        )

    perfil = resp.json()
    if not perfil.get("estado", True):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Cuenta deshabilitada")
    if perfil.get("rol") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La auditoría de evidencias es exclusiva para administradores",
        )

    usuario = {
        "id": perfil["id"],
        "correo": perfil["correo"],
        "nombre": perfil.get("nombre") or perfil["correo"],
        "rol": perfil["rol"],
    }

    _cache_identidad[llave] = (ahora + _TTL_SEG, usuario)
    while len(_cache_identidad) > _MAX_CACHE:
        _cache_identidad.popitem(last=False)

    return usuario
