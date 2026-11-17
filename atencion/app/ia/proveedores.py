# Capa adaptadora de IA con respaldo automatico.
#
# Copia adaptada de asistente/app/ia/proveedores.py (Idea 1). Se copio a proposito para no
# acoplar los dos modulos: aqui la configuracion llega por parametro (ConfigIA) en vez de leer
# un "settings" global, asi esta capa no conoce las variables de ninguno de los dos servicios.
# Si el gerente lo aprueba, en la semana 16 se puede extraer a un paquete comun para ambos.
#
# Todos los proveedores elegidos (Gemini, Groq, OpenRouter, Ollama y, si el gerente lo
# aprueba, Claude u OpenAI) exponen la API "chat/completions" compatible con OpenAI, con
# llamadas a funciones y streaming. Si uno llega a su limite (429), falla o no empieza a
# responder dentro del plazo, queda "en pausa" y la consulta pasa al siguiente.
import asyncio
import json
import time
from dataclasses import dataclass, field
from typing import AsyncIterator

import httpx

from app.core.registro import log


@dataclass(frozen=True)
class ConfigIA:
    """Parametros comunes de las llamadas a la IA (tiempos y tamano de la respuesta)."""
    conexion_seg: float = 5.0
    entre_fragmentos_seg: float = 20.0
    primer_fragmento_seg: float = 15.0
    temperatura: float = 0.3
    max_tokens: int = 700


class ErrorProveedor(Exception):
    """Fallo de un proveedor de IA. Lleva cuantos segundos conviene no usarlo y si vale la pena
    reintentar con el mismo (tropiezo puntual del modelo, no del servicio)."""

    def __init__(self, mensaje: str, pausa_seg: float = 20.0, reintentar: bool = False):
        """Guarda el motivo, la pausa y si conviene reintentar. Recibe los tres."""
        super().__init__(mensaje)
        self.pausa_seg = pausa_seg
        self.reintentar = reintentar


class SinProveedores(Exception):
    """Ningun proveedor de IA esta configurado o disponible en este momento."""


def _es_llamada_mal_formada(error) -> bool:
    """True si el proveedor rechazo una llamada a funcion mal armada por el modelo. Recibe el error."""
    return "tool_use_failed" in (json.dumps(error) if isinstance(error, dict) else str(error))


def _error_llamada_mal_formada(nombre: str, detalle: str) -> ErrorProveedor:
    """Error reintentable y sin pausa: fue un tropiezo del modelo. Recibe nombre y detalle."""
    return ErrorProveedor(f"{nombre}: llamada a función mal formada ({detalle[:160]})", pausa_seg=0.0, reintentar=True)


def timeout_http(config: ConfigIA) -> httpx.Timeout:
    """Tiempos de espera del cliente HTTP de IA. Recibe la configuracion."""
    return httpx.Timeout(connect=config.conexion_seg, read=config.entre_fragmentos_seg, write=10.0, pool=5.0)


@dataclass
class Proveedor:
    """Un proveedor compatible con la API de OpenAI: nombre, URL base, clave y modelo."""
    nombre: str
    url: str
    clave: str
    modelo: str
    config: ConfigIA = field(default_factory=ConfigIA)
    cabeceras_extra: dict = field(default_factory=dict)
    plazo_seg: float | None = None   # plazo propio (modelos locales lentos); None usa el general

    async def transmitir(
        self, mensajes: list[dict], herramientas: list[dict], http: httpx.AsyncClient
    ) -> AsyncIterator[tuple[str, object]]:
        """Pide una respuesta en streaming. Emite ('texto', fragmento) y al final ('llamadas', lista).
        Recibe mensajes, herramientas y cliente http."""
        cuerpo = {
            "model": self.modelo,
            "messages": mensajes,
            "stream": True,
            "temperature": self.config.temperatura,
            "max_tokens": self.config.max_tokens,
        }
        if herramientas:
            cuerpo["tools"] = herramientas
            cuerpo["tool_choice"] = "auto"
        cabeceras = {"Authorization": f"Bearer {self.clave}", "Content-Type": "application/json", **self.cabeceras_extra}

        acumulador = _AcumuladorLlamadas()
        plazo = self.plazo_seg or self.config.primer_fragmento_seg
        extra = {}
        if self.plazo_seg:
            extra["timeout"] = httpx.Timeout(connect=self.config.conexion_seg, read=plazo, write=10.0, pool=5.0)
        try:
            # El plazo cubre hasta el primer fragmento; se desactiva apenas llega algo, antes de
            # emitir nada, para que el corte nunca deje una respuesta a medias.
            async with asyncio.timeout(plazo) as limite:
                async with http.stream("POST", self.url.rstrip("/") + "/chat/completions", json=cuerpo,
                                       headers=cabeceras, **extra) as r:
                    if r.status_code != 200:
                        await r.aread()
                        raise _error_por_estado(self.nombre, r)
                    async for linea in r.aiter_lines():
                        if not linea.startswith("data:"):
                            continue
                        limite.reschedule(None)
                        dato = linea[5:].strip()
                        if dato == "[DONE]":
                            break
                        try:
                            trozo = json.loads(dato)
                        except ValueError:
                            continue
                        if trozo.get("error"):
                            if _es_llamada_mal_formada(trozo["error"]):
                                raise _error_llamada_mal_formada(self.nombre, str(trozo["error"]))
                            raise ErrorProveedor(f"{self.nombre}: {str(trozo['error'])[:200]}")
                        for opcion in trozo.get("choices") or []:
                            delta = opcion.get("delta") or {}
                            if delta.get("content"):
                                yield "texto", delta["content"]
                            for llamada in delta.get("tool_calls") or []:
                                acumulador.agregar(llamada)
        except TimeoutError as exc:
            raise ErrorProveedor(f"{self.nombre}: no empezó a responder en {plazo:g} s", 30.0) from exc
        except httpx.TimeoutException as exc:
            raise ErrorProveedor(f"{self.nombre}: tiempo de espera agotado") from exc
        except httpx.HTTPError as exc:
            raise ErrorProveedor(f"{self.nombre}: error de conexión ({type(exc).__name__})") from exc

        yield "llamadas", acumulador.resultado()


class _AcumuladorLlamadas:
    """Une los fragmentos de llamadas a funciones que llegan por partes en el streaming."""

    def __init__(self):
        """Empieza sin llamadas acumuladas. Sin input."""
        self._lista: list[dict] = []
        self._por_id: dict[str, dict] = {}
        self._por_indice: dict[int, dict] = {}

    def agregar(self, fragmento: dict) -> None:
        """Suma un fragmento a la llamada que corresponde (por id o por indice). Recibe el fragmento."""
        ident, indice = fragmento.get("id"), fragmento.get("index")
        llamada = None
        if ident:
            llamada = self._por_id.get(ident)
        if llamada is None and not ident and indice is not None:
            llamada = self._por_indice.get(indice)
        if llamada is None and not ident and indice is None and self._lista:
            llamada = self._lista[-1]
        if llamada is None:
            llamada = {"id": ident or f"llamada_{len(self._lista) + 1}", "type": "function",
                       "function": {"name": "", "arguments": ""}}
            self._lista.append(llamada)
            if ident:
                self._por_id[ident] = llamada
            if indice is not None:
                self._por_indice[indice] = llamada
        funcion = fragmento.get("function") or {}
        if funcion.get("name"):
            llamada["function"]["name"] += funcion["name"]
        if funcion.get("arguments"):
            argumentos = funcion["arguments"]
            llamada["function"]["arguments"] += argumentos if isinstance(argumentos, str) else json.dumps(argumentos)
        # Algunos modelos (p. ej. Gemini) envian una firma que hay que devolver tal cual.
        if fragmento.get("extra_content"):
            llamada["extra_content"] = fragmento["extra_content"]

    def resultado(self) -> list[dict]:
        """Devuelve las llamadas completas. Sin input."""
        return [ll for ll in self._lista if ll["function"]["name"]]


def _error_por_estado(nombre: str, respuesta: httpx.Response) -> ErrorProveedor:
    """Traduce el codigo HTTP de un proveedor a un error con su pausa. Recibe nombre y respuesta."""
    estado = respuesta.status_code
    if estado == 429:
        try:
            pausa = float(respuesta.headers.get("retry-after", "60"))
        except ValueError:
            pausa = 60.0
        return ErrorProveedor(f"{nombre}: límite de uso alcanzado (429)", min(max(pausa, 10.0), 600.0))
    if estado in (401, 403):
        return ErrorProveedor(f"{nombre}: clave rechazada ({estado})", 600.0)
    if estado >= 500:
        return ErrorProveedor(f"{nombre}: error del proveedor ({estado})", 30.0)
    if estado == 400 and _es_llamada_mal_formada(respuesta.text):
        return _error_llamada_mal_formada(nombre, respuesta.text)
    return ErrorProveedor(f"{nombre}: solicitud rechazada ({estado}) {respuesta.text[:200]}", 30.0)


@dataclass(frozen=True)
class DefinicionProveedor:
    """Datos de un proveedor tal como salen de la configuracion del servicio."""
    nombre: str
    url: str
    clave: str
    modelo: str
    cabeceras_extra: dict = field(default_factory=dict)
    plazo_seg: float | None = None


def construir_proveedores(orden: list[str], definiciones: dict[str, DefinicionProveedor], config: ConfigIA) -> list[Proveedor]:
    """Arma los proveedores en el orden pedido, omitiendo los que no tienen URL, clave o modelo.
    Recibe el orden, las definiciones disponibles y la configuracion comun."""
    lista = []
    for nombre in orden:
        definicion = definiciones.get(nombre)
        if definicion is None:
            log.warning("Proveedor de IA desconocido: %s", nombre)
            continue
        if definicion.url and definicion.clave and definicion.modelo:
            lista.append(Proveedor(definicion.nombre, definicion.url, definicion.clave, definicion.modelo, config,
                                   dict(definicion.cabeceras_extra), definicion.plazo_seg))
    return lista


class CadenaProveedores:
    """Prueba los proveedores en orden y salta los que estan en pausa. Recibe la lista y un reloj (pruebas)."""

    def __init__(self, proveedores: list[Proveedor], reloj=time.monotonic):
        """Guarda los proveedores en orden y el reloj. Recibe ambos."""
        self.proveedores = proveedores
        self._reloj = reloj
        self._pausados: dict[str, float] = {}

    def disponibles(self) -> list[Proveedor]:
        """Proveedores que no estan en pausa ahora. Sin input."""
        ahora = self._reloj()
        return [p for p in self.proveedores if self._pausados.get(p.nombre, 0) <= ahora]

    def estado(self) -> list[dict]:
        """Estado de cada proveedor (uso interno y administracion). Sin input."""
        ahora = self._reloj()
        return [
            {"nombre": p.nombre, "modelo": p.modelo, "pausado_seg": max(0, round(self._pausados.get(p.nombre, 0) - ahora))}
            for p in self.proveedores
        ]

    async def transmitir(
        self, mensajes: list[dict], herramientas: list[dict], http: httpx.AsyncClient
    ) -> AsyncIterator[tuple[str, object]]:
        """Igual que Proveedor.transmitir pero con respaldo. Emite tambien ('proveedor', nombre).
        Recibe mensajes, herramientas y http."""
        candidatos = self.disponibles()
        if not candidatos:
            raise SinProveedores("No hay proveedores de IA disponibles en este momento")
        ultimo_error = None
        for proveedor in candidatos:
            # Una llamada mal formada es un tropiezo del modelo: se reintenta una vez con el mismo.
            for intento in (1, 2):
                emitio_texto = False
                try:
                    yield "proveedor", proveedor.nombre
                    async for tipo, valor in proveedor.transmitir(mensajes, herramientas, http):
                        if tipo == "texto":
                            emitio_texto = True
                        yield tipo, valor
                    return
                except ErrorProveedor as exc:
                    ultimo_error = exc
                    if emitio_texto:
                        # Ya se mostro parte de la respuesta: no se puede cambiar de proveedor a mitad.
                        self._pausar(proveedor, exc)
                        raise
                    if exc.reintentar and intento == 1:
                        log.warning("Proveedor %s: reintento tras %s", proveedor.nombre, exc)
                        continue
                    self._pausar(proveedor, exc)
                    break
        raise SinProveedores(str(ultimo_error) if ultimo_error else "Sin proveedores")

    def _pausar(self, proveedor: Proveedor, exc: ErrorProveedor) -> None:
        """Deja al proveedor en pausa lo que indique el error (0 = sigue disponible). Recibe proveedor y error."""
        self._pausados[proveedor.nombre] = self._reloj() + exc.pausa_seg
        if exc.pausa_seg > 0:
            log.warning("Proveedor %s en pausa %ss: %s", proveedor.nombre, exc.pausa_seg, exc)
        else:
            log.warning("Proveedor %s falló (sin pausa): %s", proveedor.nombre, exc)
