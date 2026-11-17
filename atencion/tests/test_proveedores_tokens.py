# Capa adaptadora de IA (respaldo y configuracion propia) y tokens de conversacion.
import asyncio
import json
import time

import httpx

from app.core import tokens
from app.core.config import Settings
from app.ia.fabrica import crear_cadena, definiciones
from app.ia.proveedores import CadenaProveedores, ConfigIA, Proveedor, SinProveedores


def _sse(*trozos) -> bytes:
    """Arma un cuerpo SSE como el de chat/completions. Recibe los trozos (dict)."""
    return ("".join(f"data: {json.dumps(t)}\n\n" for t in trozos) + "data: [DONE]\n\n").encode()


def _recolectar(cadena, http):
    """Ejecuta la cadena y junta los eventos emitidos. Recibe cadena y cliente http."""
    async def correr():
        return [e async for e in cadena.transmitir([{"role": "user", "content": "hola"}], [], http)]
    return asyncio.run(correr())


def test_respaldo_cuando_el_primero_llega_a_su_limite():
    """Si Groq responde 429, se usa Gemini y Groq queda en pausa."""
    def manejador(request: httpx.Request):
        if "groq" in str(request.url):
            return httpx.Response(429, headers={"retry-after": "30"}, json={"error": "quota"})
        return httpx.Response(200, content=_sse({"choices": [{"delta": {"content": "Hola"}}]}))

    reloj = [100.0]
    cadena = CadenaProveedores(
        [Proveedor("groq", "http://groq.test", "k", "m"), Proveedor("gemini", "http://gemini.test", "k", "m")],
        reloj=lambda: reloj[0],
    )
    eventos = _recolectar(cadena, httpx.AsyncClient(transport=httpx.MockTransport(manejador)))
    assert ("texto", "Hola") in eventos
    assert [v for t, v in eventos if t == "proveedor"] == ["groq", "gemini"]
    assert [p.nombre for p in cadena.disponibles()] == ["gemini"]
    reloj[0] += 31
    assert [p.nombre for p in cadena.disponibles()] == ["groq", "gemini"]


def test_sin_proveedores_disponibles():
    """Si todos fallan, se informa que no hay proveedores."""
    http = httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(500)))
    cadena = CadenaProveedores([Proveedor("gemini", "http://g.test", "k", "m")])
    try:
        _recolectar(cadena, http)
        assert False, "debio fallar"
    except SinProveedores:
        pass


def test_la_configuracion_llega_por_parametro():
    """Temperatura y tope de tokens salen de ConfigIA, no de un settings global."""
    recibido = {}

    def manejador(request: httpx.Request):
        recibido.update(json.loads(request.content))
        return httpx.Response(200, content=_sse({"choices": [{"delta": {"content": "ok"}}]}))

    proveedor = Proveedor("groq", "http://groq.test", "k", "m", ConfigIA(temperatura=0.1, max_tokens=99))
    _recolectar(CadenaProveedores([proveedor]), httpx.AsyncClient(transport=httpx.MockTransport(manejador)))
    assert recibido["temperature"] == 0.1 and recibido["max_tokens"] == 99


def test_claves_propias_vacias_usan_las_del_panel():
    """Sin ATENCION_*_API_KEY se usan GROQ/GEMINI/OPENROUTER_API_KEY; con clave propia, manda la propia."""
    s = Settings(_env_file=None, ATENCION_GROQ_API_KEY="", GROQ_API_KEY="del-panel",
                 ATENCION_GEMINI_API_KEY="propia", GEMINI_API_KEY="del-panel", OPENROUTER_API_KEY="del-panel")
    d = definiciones(s)
    assert d["groq"].clave == "del-panel"
    assert d["gemini"].clave == "propia"
    assert d["openrouter"].clave == "del-panel"


def test_omite_proveedores_sin_clave_y_respeta_el_orden():
    """Solo quedan los proveedores con clave, en el orden configurado."""
    s = Settings(_env_file=None, ATENCION_PROVEEDORES="openrouter,groq,gemini,ollama",
                 GROQ_API_KEY="k", OPENROUTER_API_KEY="k", GEMINI_API_KEY="", ATENCION_GEMINI_API_KEY="")
    assert [p.nombre for p in crear_cadena(s).proveedores] == ["openrouter", "groq"]
    assert [p.nombre for p in crear_cadena(s, ["groq"]).proveedores] == ["groq"]


def test_token_de_conversacion_valido():
    """Un token recien emitido devuelve su conversacion."""
    assert tokens.validar(tokens.emitir("a" * 32)) == "a" * 32


def test_token_alterado_o_vencido_no_vale():
    """Cambiar el id, la firma o el vencimiento invalida el token."""
    token = tokens.emitir("a" * 32)
    ident, vence, firma = token.split(".")
    assert tokens.validar(f"{'b' * 32}.{vence}.{firma}") is None
    assert tokens.validar(f"{ident}.{int(vence) + 999}.{firma}") is None
    assert tokens.validar(token[:-1] + ("0" if token[-1] != "0" else "1")) is None
    assert tokens.validar(token, ahora=time.time() + 10 ** 6) is None
    assert tokens.validar("basura") is None
