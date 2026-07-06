# Tokens JWT cortos y acotados para el portal publico. Reutiliza el SECRET/ALGO
# de la app. El scope distingue persona de empresa y el sub ata el token a un
# recurso concreto (codigo de pedido o codigo de acceso de la empresa).
from datetime import timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError

from app.core.config import settings
from app.core.security import create_access_token, decode_access_token

_bearer = HTTPBearer(auto_error=False)


def crear_token_persona(codigo: str) -> str:
    """Emite un token de portal para un pedido. Recibe el codigo del pedido."""
    return create_access_token(
        {"sub": codigo, "scope": "portal_persona"},
        expires_delta=timedelta(minutes=settings.PORTAL_TOKEN_EXPIRE_MIN),
    )


def crear_token_empresa(codigo_acceso: str) -> str:
    """Emite un token de portal para una empresa. Recibe su codigo de acceso."""
    return create_access_token(
        {"sub": codigo_acceso, "scope": "portal_empresa"},
        expires_delta=timedelta(minutes=10),
    )


def _decodificar(cred: HTTPAuthorizationCredentials | None, scope: str) -> dict:
    """Valida el Bearer y su scope; devuelve el payload. Recibe credencial y scope esperado."""
    invalido = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Sesion de portal invalida o expirada",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if cred is None or not cred.credentials:
        raise invalido
    try:
        payload = decode_access_token(cred.credentials)
    except JWTError:
        raise invalido
    if payload.get("scope") != scope:
        raise invalido
    return payload


def requiere_token_persona(codigo: str, cred: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> str:
    """Dependencia: exige token de persona valido para ESE codigo de pedido. Recibe codigo (path).
    Normaliza a mayusculas en ambos lados (el sub se emite en mayusculas) para no rechazar un
    token valido por diferencia de casing. Devuelve el codigo normalizado ligado al token."""
    payload = _decodificar(cred, "portal_persona")
    codigo_norm = (codigo or "").upper()
    if payload.get("sub") != codigo_norm:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="El token no corresponde a este pedido")
    return codigo_norm


def requiere_token_empresa(cred: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> str:
    """Dependencia: exige token de empresa valido; devuelve el codigo de acceso. Sin input extra."""
    payload = _decodificar(cred, "portal_empresa")
    return payload["sub"]
