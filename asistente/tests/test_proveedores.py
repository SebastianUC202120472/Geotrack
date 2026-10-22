# Capa adaptadora: streaming compatible con OpenAI y respaldo automatico entre proveedores.
import asyncio
import json

import httpx

from app.ia.proveedores import CadenaProveedores, Proveedor, SinProveedores, _AcumuladorLlamadas


def _sse(*trozos) -> bytes:
    """Arma un cuerpo SSE como el de chat/completions. Recibe los trozos (dict)."""
    return ("".join(f"data: {json.dumps(t)}\n\n" for t in trozos) + "data: [DONE]\n\n").encode()


def _recolectar(cadena, http):
    """Ejecuta la cadena y junta los eventos emitidos. Recibe cadena y cliente http."""
    async def correr():
        return [e async for e in cadena.transmitir([{"role": "user", "content": "hola"}], [], http)]
    return asyncio.run(correr())


def test_respaldo_cuando_el_primero_llega_a_su_limite():
    """Si Gemini responde 429, se usa Groq y Gemini queda en pausa."""
    def manejador(request: httpx.Request):
        if "gemini" in str(request.url):
            return httpx.Response(429, headers={"retry-after": "30"}, json={"error": "quota"})
        return httpx.Response(200, content=_sse({"choices": [{"delta": {"content": "Hola"}}]}))

    http = httpx.AsyncClient(transport=httpx.MockTransport(manejador))
    reloj = [100.0]
    cadena = CadenaProveedores(
        [Proveedor("gemini", "http://gemini.test", "k", "m"), Proveedor("groq", "http://groq.test", "k", "m")],
        reloj=lambda: reloj[0],
    )
    eventos = _recolectar(cadena, http)
    assert ("texto", "Hola") in eventos
    assert [v for t, v in eventos if t == "proveedor"] == ["gemini", "groq"]
    assert [p.nombre for p in cadena.disponibles()] == ["groq"]
    reloj[0] += 31
    assert [p.nombre for p in cadena.disponibles()] == ["gemini", "groq"]


def test_sin_proveedores_disponibles():
    """Si todos fallan, se informa que no hay proveedores."""
    http = httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(500)))
    cadena = CadenaProveedores([Proveedor("gemini", "http://g.test", "k", "m")])
    try:
        _recolectar(cadena, http)
        assert False, "debio fallar"
    except SinProveedores:
        pass


def test_llamadas_a_funciones_por_partes():
    """Los argumentos de una llamada llegan en varios trozos y se unen."""
    cuerpo = _sse(
        {"choices": [{"delta": {"tool_calls": [{"index": 0, "id": "a1", "function": {"name": "buscar_pedidos", "arguments": "{\"cli"}}]}}]},
        {"choices": [{"delta": {"tool_calls": [{"index": 0, "function": {"arguments": "ente\": \"Ripley\"}"}}]}}]},
    )
    http = httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(200, content=cuerpo)))
    cadena = CadenaProveedores([Proveedor("groq", "http://groq.test", "k", "m")])
    llamadas = dict(_recolectar(cadena, http))["llamadas"]
    assert llamadas[0]["function"] == {"name": "buscar_pedidos", "arguments": "{\"cliente\": \"Ripley\"}"}


def test_acumulador_separa_llamadas_paralelas_sin_indice():
    """Dos llamadas con id distinto y sin indice se guardan por separado (y conservan la firma)."""
    acum = _AcumuladorLlamadas()
    acum.agregar({"id": "x", "function": {"name": "a", "arguments": "{}"}, "extra_content": {"google": {"thought_signature": "s"}}})
    acum.agregar({"id": "y", "function": {"name": "b", "arguments": "{}"}})
    resultado = acum.resultado()
    assert [r["function"]["name"] for r in resultado] == ["a", "b"]
    assert resultado[0]["extra_content"]["google"]["thought_signature"] == "s"
