# Dependencias comunes de los endpoints publicos del modulo.
# El visitante es anonimo: no hay token de usuario del panel. Lo que lo identifica es el
# token firmado de SU conversacion (cabecera X-Conversacion), que recibe al aceptar el aviso.
from fastapi import HTTPException, Request, status

from app.core import tokens
from app.core.config import settings

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
