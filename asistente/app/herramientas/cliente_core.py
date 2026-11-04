# Cliente hacia la API del nucleo.
#
# - get: solo GET, y solo a una lista cerrada de rutas de consulta que ya existen.
# - post_accion: solo POST, a OTRA lista cerrada (las 3 acciones con confirmacion). Solo lo
#   llama el endpoint de confirmar, despues del clic del usuario: nunca el modelo ni el chat.
# - Cada peticion viaja con el token del usuario conectado: el nucleo aplica sus
#   propios permisos, asi que por el chat nadie ve ni hace mas de lo que puede en el panel.
import re

import httpx

from app.core.config import settings

# Rutas de consulta permitidas (relativas a /api). Nada que cree, edite o borre.
_RUTAS_PERMITIDAS = [
    re.compile(p)
    for p in (
        r"^/usuarios/yo$",
        r"^/pedidos/$",
        r"^/pedidos/zonas/por-enrutar$",
        r"^/dashboard/resumen$",
        r"^/dashboard/flota$",
        r"^/dashboard/clientes$",
        r"^/dashboard/flota/ubicaciones$",
        r"^/dashboard/pedidos/[A-Za-z0-9._-]{1,40}/historial$",
        r"^/conductores/$",
        r"^/incidencias$",
        r"^/reportes/$",
        r"^/correos/conversaciones$",
        r"^/correos/conversaciones/\d{1,9}$",
        r"^/almacen/recojos$",
        r"^/almacen/observados$",
        r"^/almacen/retornos/rutas$",
        r"^/almacen/retornos/rutas/\d{1,9}$",
        r"^/almacen/flota/ubicaciones-recojo$",
    )
]


# Rutas de escritura permitidas (relativas a /api): una por accion de acciones.ACCIONES.
_ESCRITURAS_PERMITIDAS = [
    re.compile(p)
    for p in (
        r"^/pedidos/\d{1,9}/reprogramar$",
        r"^/almacen/pedidos/\d{1,9}/resolver-observado$",
        r"^/almacen/retornos/rutas/\d{1,9}/escanear$",
    )
]


class ErrorCore(Exception):
    """Error al consultar el nucleo (caido, respuesta invalida, etc.)."""


class SesionInvalida(ErrorCore):
    """El token del usuario ya no es valido (401)."""


class SinPermiso(ErrorCore):
    """El rol del usuario no puede ver ese dato en el panel (403)."""


class NoEncontrado(ErrorCore):
    """El dato consultado no existe (404)."""


class Rechazado(ErrorCore):
    """El nucleo rechazo la escritura por una regla de negocio (400/409/422); trae su mensaje."""


def ruta_permitida(ruta: str) -> bool:
    """Dice si una ruta esta en la lista cerrada de consultas. Recibe la ruta relativa a /api."""
    return any(p.match(ruta) for p in _RUTAS_PERMITIDAS)


def escritura_permitida(ruta: str) -> bool:
    """Dice si una ruta esta en la lista cerrada de escrituras. Recibe la ruta relativa a /api."""
    return any(p.match(ruta) for p in _ESCRITURAS_PERMITIDAS)


class ClienteCore:
    """Consulta la API del nucleo con el token del usuario. Recibe token y un cliente httpx opcional (pruebas)."""

    def __init__(self, token: str, http: httpx.AsyncClient | None = None):
        self._token = token
        self._http = http
        self.consultas = 0

    async def get(self, ruta: str, params: dict | None = None):
        """Hace un GET a una ruta permitida y devuelve el JSON. Recibe ruta y parametros."""
        if not ruta_permitida(ruta):
            raise ErrorCore(f"Ruta no permitida para el asistente: {ruta}")
        params = {k: v for k, v in (params or {}).items() if v not in (None, "")}
        return await self._enviar("GET", ruta, params=params)

    async def post_accion(self, ruta: str, cuerpo: dict | None = None):
        """Hace un POST a una ruta de la lista cerrada de acciones (sin reintentos). Recibe ruta y cuerpo.
        Si el nucleo rechaza la operacion lanza Rechazado con su mensaje."""
        if not escritura_permitida(ruta):
            raise ErrorCore(f"Escritura no permitida para el asistente: {ruta}")
        return await self._enviar("POST", ruta, cuerpo=cuerpo)

    async def _enviar(self, metodo: str, ruta: str, params: dict | None = None, cuerpo: dict | None = None):
        """Envia la peticion con el token del usuario y traduce los errores. Recibe metodo, ruta, params y cuerpo."""
        cabeceras = {"Authorization": f"Bearer {self._token}", "Accept": "application/json"}
        url = settings.ASISTENTE_CORE_API_URL.rstrip("/") + ruta
        opciones = {"params": params, "headers": cabeceras}
        if cuerpo is not None:
            opciones["json"] = cuerpo
        self.consultas += 1
        try:
            if self._http is not None:
                respuesta = await self._http.request(metodo, url, **opciones)
            else:
                async with httpx.AsyncClient(timeout=settings.ASISTENTE_CORE_TIMEOUT_SEG) as http:
                    respuesta = await http.request(metodo, url, **opciones)
        except httpx.HTTPError as exc:
            raise ErrorCore("El sistema GeoTrack no respondió") from exc

        if respuesta.status_code == 401:
            raise SesionInvalida("Sesión expirada")
        if respuesta.status_code == 403:
            raise SinPermiso("Tu rol no tiene acceso a este dato")
        if respuesta.status_code == 404:
            raise NoEncontrado(_detalle(respuesta) or "No encontrado")
        if metodo != "GET" and respuesta.status_code in (400, 409, 422):
            raise Rechazado(_detalle(respuesta) or "El sistema rechazó la operación")
        if respuesta.status_code >= 400:
            raise ErrorCore(f"El sistema respondió con error {respuesta.status_code}")
        try:
            return respuesta.json()
        except ValueError as exc:
            raise ErrorCore("Respuesta inválida del sistema") from exc


def _detalle(respuesta: httpx.Response) -> str | None:
    """Extrae el campo 'detail' de un error del nucleo. Recibe la respuesta."""
    try:
        detalle = respuesta.json().get("detail")
        return detalle if isinstance(detalle, str) else None
    except (ValueError, AttributeError):
        return None
