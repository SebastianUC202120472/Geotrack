# Dependencias comunes de los endpoints publicos del modulo.
# El visitante es anonimo: no hay token de usuario del panel. Lo que lo identifica es el
# token firmado de SU conversacion (cabecera X-Conversacion), que recibe al aceptar el aviso.
import hashlib
import time
from collections import OrderedDict

import httpx
from fastapi import HTTPException, Request, status

from app.core import tokens
from app.core.config import settings
from app.core.limites import limitador

CABECERA_CONVERSACION = "X-Conversacion"


def exigir_activo() -> None:
    """Corta la peticion si el modulo esta apagado por variable de entorno. Sin input."""
    if not settings.ATENCION_ENABLED:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "El asistente de atención está desactivado")


def verificar_origen(request: Request) -> None:
    """Acepta escrituras solo desde el sitio de SAVA (cabecera Origin). Recibe la peticion.
    Complementa a CORS: el navegador siempre envia Origin en un POST; un script sin navegador
    tambien queda frenado por los limites por IP y el token de conversacion."""
    permitidos = settings.cors_origins_list
    if not permitidos:
        return
    origen = (request.headers.get("origin") or "").rstrip("/")
    if origen not in permitidos:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Origen no permitido")


def conversacion_del_token(request: Request) -> str:
    """Id de la conversacion segun su token firmado y vigente; 401 si falta o no vale. Recibe la peticion."""
    conversacion_id = tokens.validar(request.headers.get(CABECERA_CONVERSACION))
    if not conversacion_id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "La conversación venció. Vuelve a abrir el chat.")
    return conversacion_id


# --- Administracion (pantalla del panel) -------------------------------------------------------
# La identidad del administrador NO se decodifica aqui: se pregunta al nucleo (/usuarios/yo) con
# el mismo token del panel, igual que en el asistente del panel (Idea 1). Asi se respetan la
# desactivacion de cuentas y los roles del nucleo sin conocer su clave secreta.
_TTL_ADMIN_SEG = 60
_MAX_CACHE_ADMIN = 200
_cache_admin: OrderedDict[str, tuple[float, dict]] = OrderedDict()


def limpiar_cache_admin() -> None:
    """Vacia la cache de identidades de administradores (pruebas). Sin input."""
    _cache_admin.clear()


async def obtener_admin(request: Request) -> dict:
    """Valida el token del panel contra el nucleo y exige rol admin; devuelve {id, correo, nombre}. Recibe la peticion."""
    exigir_activo()
    tipo, _, token = request.headers.get("authorization", "").partition(" ")
    token = token.strip()
    if tipo.lower() != "bearer" or not token or len(token) > 4096:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Falta iniciar sesión")
    llave = hashlib.sha256(token.encode()).hexdigest()
    ahora = time.monotonic()
    guardado = _cache_admin.get(llave)
    if guardado and guardado[0] > ahora:
        return _limitar_admin(guardado[1])
    url = settings.ATENCION_CORE_API_URL.rstrip("/") + "/usuarios/yo"
    try:
        r = await request.app.state.http_core.get(url, headers={"Authorization": f"Bearer {token}"},
                                                  timeout=settings.ATENCION_CORE_TIMEOUT_SEG)
    except httpx.HTTPError:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "No se pudo validar la sesión")
    if r.status_code == 401:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Tu sesión expiró")
    if r.status_code != 200:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo para administradores")
    perfil = r.json()
    if perfil.get("rol") != "admin" or not perfil.get("estado", True):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo para administradores")
    admin = {"id": int(perfil["id"]), "correo": str(perfil.get("correo", ""))[:120], "nombre": perfil.get("nombre") or ""}
    _cache_admin[llave] = (ahora + _TTL_ADMIN_SEG, admin)
    if len(_cache_admin) > _MAX_CACHE_ADMIN:
        _cache_admin.popitem(last=False)
    return _limitar_admin(admin)


def _limitar_admin(admin: dict) -> dict:
    """Aplica el tope de peticiones por minuto de cada administrador. Recibe el administrador."""
    if not limitador.permitir(f"admin:{admin['id']}", 120, 60):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Demasiadas solicitudes. Espera un momento.")
    return admin
