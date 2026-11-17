# Cliente de la API PUBLICA del portal en el nucleo (backend/app/api/portal.py).
# El asistente nunca toca la base del nucleo: usa los mismos endpoints que el portal web,
# con sus validaciones, su verificacion por DNI, su bloqueo progresivo y sus limites.
#
# IP del visitante: el nucleo limita por IP (X-Real-IP). Si este servicio no la reenviara,
# todos los visitantes del chat compartirian la IP del contenedor y un solo limite para todo
# el sitio. Por eso cada llamada lleva el X-Real-IP del visitante (que Nginx escribio).
# Ver docs/hallazgos_nucleo.md, punto 2.
import re
from urllib.parse import quote

import httpx

from app.core.config import settings

_RE_CODIGO = re.compile(r"^[A-Z0-9][A-Z0-9-]{1,28}[A-Z0-9]$")


class ErrorPortal(Exception):
    """Fallo generico al consultar el portal (caido, respuesta inesperada)."""


class NoEncontrado(ErrorPortal):
    """El pedido no existe."""


class DatosRetirados(ErrorPortal):
    """El pedido es antiguo y sus datos se retiraron (410)."""


class VerificacionFallida(ErrorPortal):
    """Los digitos del DNI no coinciden. Lleva cuantos intentos quedan."""

    def __init__(self, restantes: int | None):
        """Guarda los intentos restantes. Recibe el numero (o None)."""
        super().__init__("verificación fallida")
        self.restantes = restantes


class Bloqueado(ErrorPortal):
    """Demasiados intentos: el portal bloqueo la consulta. Lleva los segundos de espera."""

    def __init__(self, segundos: int | None):
        """Guarda los segundos de bloqueo. Recibe el numero (o None)."""
        super().__init__("bloqueado")
        self.segundos = segundos


class SesionVencida(ErrorPortal):
    """El token de portal del pedido vencio (15 min): hay que verificar de nuevo."""


class Rechazado(ErrorPortal):
    """El portal rechazo la operacion (409 no reprogramable, 400 franja invalida, 422 datos). Lleva el motivo."""


def codigo_valido(codigo: str) -> str | None:
    """Normaliza un codigo de pedido (mayusculas, sin espacios) o None si no tiene forma de codigo. Recibe el texto."""
    limpio = re.sub(r"\s+", "", (codigo or "")).upper()
    return limpio if _RE_CODIGO.match(limpio) else None


def _detalle(r: httpx.Response):
    """El campo 'detail' de una respuesta de error del portal, si lo hay. Recibe la respuesta."""
    try:
        return r.json().get("detail")
    except (ValueError, AttributeError):
        return None


class ClientePortal:
    """Llama a los endpoints publicos del portal en nombre de un visitante. Recibe el cliente http y su IP."""

    def __init__(self, http: httpx.AsyncClient, ip_visitante: str):
        """Guarda el cliente http y la IP real del visitante. Recibe ambos."""
        self._http = http
        self._cabeceras = {"X-Real-IP": ip_visitante}
        self._base = settings.ATENCION_CORE_API_URL.rstrip("/") + "/portal"

    async def _pedir(self, metodo: str, ruta: str, token: str | None = None, **kwargs) -> httpx.Response:
        """Hace la llamada y traduce los errores de red. Recibe metodo, ruta, token de portal y argumentos."""
        cabeceras = dict(self._cabeceras)
        if token:
            cabeceras["Authorization"] = f"Bearer {token}"
        try:
            return await self._http.request(metodo, self._base + ruta, headers=cabeceras,
                                            timeout=settings.ATENCION_CORE_TIMEOUT_SEG, **kwargs)
        except httpx.HTTPError as exc:
            raise ErrorPortal(f"portal no disponible ({type(exc).__name__})") from exc

    @staticmethod
    def _revisar(r: httpx.Response) -> dict:
        """Devuelve el JSON si salio bien o lanza el error que corresponde. Recibe la respuesta."""
        if r.status_code == 200:
            try:
                return r.json()
            except ValueError as exc:
                raise ErrorPortal("respuesta inválida del portal") from exc
        detalle = _detalle(r)
        if r.status_code == 404:
            raise NoEncontrado("no encontrado")
        if r.status_code == 410:
            raise DatosRetirados("datos retirados")
        if r.status_code == 401:
            if isinstance(detalle, dict) and "intentosRestantes" in detalle:
                raise VerificacionFallida(detalle.get("intentosRestantes"))
            raise SesionVencida("sesión de portal vencida")
        if r.status_code == 429:
            segundos = detalle.get("bloqueadoSegundos") if isinstance(detalle, dict) else None
            raise Bloqueado(segundos)
        if r.status_code in (400, 403, 409, 422):
            raise Rechazado(detalle if isinstance(detalle, str) else "solicitud rechazada")
        raise ErrorPortal(f"el portal respondió {r.status_code}")

    async def resumen(self, codigo: str) -> dict:
        """Resumen enmascarado de un pedido, antes de verificar. Recibe el codigo."""
        return self._revisar(await self._pedir("POST", f"/pedidos/{quote(codigo)}/buscar"))

    async def verificar(self, codigo: str, digitos: str) -> dict:
        """Verifica con los ultimos 4 digitos del DNI; devuelve {token, pedido}. Recibe codigo y digitos."""
        return self._revisar(await self._pedir("POST", f"/pedidos/{quote(codigo)}/verificar", json={"dni": digitos}))

    async def detalle(self, codigo: str, token: str) -> dict:
        """Detalle de un pedido ya verificado. Recibe codigo y token de portal."""
        return self._revisar(await self._pedir("GET", f"/pedidos/{quote(codigo)}", token))

    async def franjas(self) -> list[str]:
        """Franjas vigentes para reprogramar. Sin input."""
        franjas = self._revisar(await self._pedir("GET", "/franjas")).get("franjas") or []
        return [f for f in franjas if isinstance(f, str)]

    async def reprogramar(self, codigo: str, franja: str, token: str) -> dict:
        """Registra la solicitud de reprogramacion. Recibe codigo, franja y token de portal."""
        return self._revisar(await self._pedir("POST", f"/pedidos/{quote(codigo)}/reprogramar", token,
                                               json={"franja": franja}))

    async def contacto(self, datos: dict) -> dict:
        """Registra un contacto de empresa con el formulario existente. Recibe los datos del lead."""
        return self._revisar(await self._pedir("POST", "/contacto", json={**datos, "hp": None}))
