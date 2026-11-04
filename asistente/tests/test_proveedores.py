# Capa adaptadora: streaming compatible con OpenAI y respaldo automatico entre proveedores.
import asyncio
import json

import httpx

import pytest

from app.core.config import settings
from app.ia.proveedores import (
    CadenaProveedores,
    ErrorProveedor,
    Proveedor,
    SinProveedores,
    _AcumuladorLlamadas,
    construir_proveedores,
    timeout_http_ia,
)


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


# --- Plazo del primer fragmento, respaldo por limite y caida total -------------------------

def _modelo(request: httpx.Request) -> str:
    """Modelo pedido en el cuerpo de chat/completions (los dos Groq comparten URL). Recibe la peticion."""
    return json.loads(request.content)["model"]


def _trozo(texto: str) -> bytes:
    """Un fragmento SSE de texto. Recibe el texto."""
    return f"data: {json.dumps({'choices': [{'delta': {'content': texto}}]})}\n\n".encode()


class _FlujoLento(httpx.AsyncByteStream):
    """Cuerpo SSE que se entrega por partes con pausas. Recibe una lista de bytes o segundos de espera."""

    def __init__(self, partes):
        self.partes = partes

    async def __aiter__(self):
        for parte in self.partes:
            if isinstance(parte, (int, float)):
                await asyncio.sleep(parte)
            else:
                yield parte


def test_proveedor_que_no_responde_a_tiempo_pasa_al_siguiente(monkeypatch):
    """Si Gemini no manda nada dentro del plazo, se corta, queda en pausa y responde Groq."""
    monkeypatch.setattr(settings, "ASISTENTE_IA_PRIMER_FRAGMENTO_SEG", 0.05)

    async def manejador(request: httpx.Request):
        if "gemini" in str(request.url):
            await asyncio.sleep(1)   # ni siquiera llegan las cabeceras
        return httpx.Response(200, content=_sse({"choices": [{"delta": {"content": "Hola"}}]}))

    http = httpx.AsyncClient(transport=httpx.MockTransport(manejador))
    cadena = CadenaProveedores([Proveedor("gemini", "http://gemini.test", "k", "m"), Proveedor("groq", "http://groq.test", "k", "m")])
    eventos = _recolectar(cadena, http)
    assert ("texto", "Hola") in eventos
    assert [v for t, v in eventos if t == "proveedor"] == ["gemini", "groq"]
    assert [p.nombre for p in cadena.disponibles()] == ["groq"]


def test_comentarios_keepalive_no_cuentan_como_respuesta(monkeypatch):
    """Un proveedor que solo manda comentarios SSE (': ping') y se queda callado tambien se corta."""
    monkeypatch.setattr(settings, "ASISTENTE_IA_PRIMER_FRAGMENTO_SEG", 0.05)
    http = httpx.AsyncClient(transport=httpx.MockTransport(
        lambda r: httpx.Response(200, stream=_FlujoLento([b": ping\n\n", 1, b": ping\n\n"]))
    ))
    proveedor = Proveedor("gemini", "http://gemini.test", "k", "m")

    async def correr():
        return [e async for e in proveedor.transmitir([{"role": "user", "content": "hola"}], [], http)]

    with pytest.raises(ErrorProveedor, match="no empezó a responder"):
        asyncio.run(correr())


def test_respuesta_lenta_ya_iniciada_no_se_corta(monkeypatch):
    """El plazo solo vale para el PRIMER fragmento: si la respuesta ya empezo, una pausa larga no la corta."""
    monkeypatch.setattr(settings, "ASISTENTE_IA_PRIMER_FRAGMENTO_SEG", 0.05)
    http = httpx.AsyncClient(transport=httpx.MockTransport(
        lambda r: httpx.Response(200, stream=_FlujoLento([_trozo("Hola "), 0.2, _trozo("Ana"), b"data: [DONE]\n\n"]))
    ))
    cadena = CadenaProveedores([Proveedor("gemini", "http://gemini.test", "k", "m")])
    eventos = _recolectar(cadena, http)
    assert "".join(v for t, v in eventos if t == "texto") == "Hola Ana"
    assert [p.nombre for p in cadena.disponibles()] == ["gemini"]


def test_429_pasa_al_segundo_modelo_de_groq():
    """Gemini saturado (503) y Groq 120b con limite (429): responde el modelo de respaldo de Groq."""
    def manejador(request: httpx.Request):
        if "gemini" in str(request.url):
            return httpx.Response(503, json={"error": "high demand"})
        if _modelo(request) == "openai/gpt-oss-120b":
            return httpx.Response(429, headers={"retry-after": "45"}, json={"error": "rate limit"})
        return httpx.Response(200, content=_sse({"choices": [{"delta": {"content": "Respondo yo"}}]}))

    http = httpx.AsyncClient(transport=httpx.MockTransport(manejador))
    reloj = [0.0]
    cadena = CadenaProveedores([
        Proveedor("gemini", "http://gemini.test", "k", "gemini-3.5-flash-lite"),
        Proveedor("groq", "http://groq.test", "k", "openai/gpt-oss-120b"),
        Proveedor("groq_respaldo", "http://groq.test", "k", "openai/gpt-oss-20b"),
    ], reloj=lambda: reloj[0])
    eventos = _recolectar(cadena, http)
    assert ("texto", "Respondo yo") in eventos
    assert [v for t, v in eventos if t == "proveedor"] == ["gemini", "groq", "groq_respaldo"]
    # La pausa es por modelo: el 120b respeta su retry-after y el de respaldo sigue disponible.
    assert [p.nombre for p in cadena.disponibles()] == ["groq_respaldo"]
    reloj[0] += 31
    assert [p.nombre for p in cadena.disponibles()] == ["gemini", "groq_respaldo"]


def test_todos_caidos_y_luego_todos_en_pausa():
    """Si todos fallan se lanza SinProveedores; en la pregunta siguiente ni se los llama (estan en pausa)."""
    llamados = []

    def manejador(request: httpx.Request):
        llamados.append(str(request.url))
        return httpx.Response(429 if "groq" in str(request.url) else 503)

    http = httpx.AsyncClient(transport=httpx.MockTransport(manejador))
    cadena = CadenaProveedores([Proveedor("gemini", "http://gemini.test", "k", "m"), Proveedor("groq", "http://groq.test", "k", "m")])
    with pytest.raises(SinProveedores):
        _recolectar(cadena, http)
    assert len(llamados) == 2
    with pytest.raises(SinProveedores):
        _recolectar(cadena, http)
    assert len(llamados) == 2


def test_llamada_mal_formada_se_reintenta_sin_pausar():
    """Groq rechaza una funcion inventada (tool_use_failed): se reintenta una vez con el mismo modelo."""
    intentos = []

    def manejador(request: httpx.Request):
        intentos.append(_modelo(request))
        if len(intentos) == 1:
            return httpx.Response(200, content=_sse({"error": {
                "message": "attempted to call tool 'retorno_almacen' which was not in request.tools",
                "type": "invalid_request_error", "code": "tool_use_failed"}}))
        return httpx.Response(200, content=_sse({"choices": [{"delta": {"content": "Sin retornos"}}]}))

    http = httpx.AsyncClient(transport=httpx.MockTransport(manejador))
    cadena = CadenaProveedores([Proveedor("groq", "http://groq.test", "k", "openai/gpt-oss-120b")])
    eventos = _recolectar(cadena, http)
    assert ("texto", "Sin retornos") in eventos
    assert intentos == ["openai/gpt-oss-120b", "openai/gpt-oss-120b"]
    assert [p.nombre for p in cadena.disponibles()] == ["groq"]


def test_llamada_mal_formada_dos_veces_pasa_al_siguiente_sin_pausar():
    """Si el modelo vuelve a armar mal la llamada (400 tool_use_failed), se pasa al siguiente y no queda en pausa."""
    def manejador(request: httpx.Request):
        if _modelo(request) == "openai/gpt-oss-120b":
            return httpx.Response(400, json={"error": {"message": "parameters for tool recojos_almacen did not match schema",
                                                       "type": "invalid_request_error", "code": "tool_use_failed"}})
        return httpx.Response(200, content=_sse({"choices": [{"delta": {"content": "ok"}}]}))

    http = httpx.AsyncClient(transport=httpx.MockTransport(manejador))
    cadena = CadenaProveedores([
        Proveedor("groq", "http://groq.test", "k", "openai/gpt-oss-120b"),
        Proveedor("groq_respaldo", "http://groq.test", "k", "openai/gpt-oss-20b"),
    ])
    eventos = _recolectar(cadena, http)
    assert [v for t, v in eventos if t == "proveedor"] == ["groq", "groq", "groq_respaldo"]
    assert ("texto", "ok") in eventos
    assert [p.nombre for p in cadena.disponibles()] == ["groq", "groq_respaldo"]


def test_orden_de_proveedores_configurable(monkeypatch):
    """El orden sale de ASISTENTE_PROVEEDORES; groq_respaldo usa la clave de Groq y se omite sin modelo."""
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "g")
    monkeypatch.setattr(settings, "GROQ_API_KEY", "q")
    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "")
    monkeypatch.setattr(settings, "OLLAMA_URL", "")
    monkeypatch.setattr(settings, "GROQ_MODELO", "openai/gpt-oss-120b")
    monkeypatch.setattr(settings, "GROQ_MODELO_RESPALDO", "openai/gpt-oss-20b")

    monkeypatch.setattr(settings, "ASISTENTE_PROVEEDORES", "gemini,groq,groq_respaldo,openrouter,ollama")
    assert [(p.nombre, p.modelo) for p in construir_proveedores()] == [
        ("gemini", settings.GEMINI_MODELO), ("groq", "openai/gpt-oss-120b"), ("groq_respaldo", "openai/gpt-oss-20b"),
    ]
    monkeypatch.setattr(settings, "ASISTENTE_PROVEEDORES", "groq,groq_respaldo,gemini,openrouter,ollama")
    assert [p.nombre for p in construir_proveedores()] == ["groq", "groq_respaldo", "gemini"]
    monkeypatch.setattr(settings, "GROQ_MODELO_RESPALDO", "")
    assert [p.nombre for p in construir_proveedores()] == ["groq", "gemini"]


def test_valores_por_defecto():
    """Por defecto: Gemini -> Groq 120b -> Groq 20b -> OpenRouter -> Ollama, con plazos de 20 s."""
    from app.core.config import Settings
    campos = Settings.model_fields
    assert campos["ASISTENTE_PROVEEDORES"].default == "gemini,groq,groq_respaldo,openrouter,ollama"
    assert campos["GROQ_MODELO_RESPALDO"].default == "openai/gpt-oss-20b"
    assert campos["ASISTENTE_IA_TIMEOUT_SEG"].default == 20.0
    assert campos["ASISTENTE_IA_PRIMER_FRAGMENTO_SEG"].default == 20.0


def test_timeouts_separados_del_cliente_http():
    """Conexion corta y espera entre fragmentos de 20 s, en vez de un unico timeout de 45 s."""
    t = timeout_http_ia()
    assert (t.connect, t.read, t.write, t.pool) == (5.0, 20.0, 10.0, 5.0)


def test_ollama_tiene_plazo_propio(monkeypatch):
    """Ollama local (lento sin tarjeta de video) espera mas; los de la nube siguen con el plazo corto."""
    monkeypatch.setattr(settings, "ASISTENTE_PROVEEDORES", "gemini,ollama")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "g")
    monkeypatch.setattr(settings, "OLLAMA_URL", "http://host.docker.internal:11434")
    monkeypatch.setattr(settings, "OLLAMA_TIMEOUT_SEG", 120.0)
    gemini, ollama = construir_proveedores()
    assert gemini.plazo_seg is None and ollama.plazo_seg == 120.0
    assert ollama.url == "http://host.docker.internal:11434/v1"

    # Con plazo propio, una respuesta que tarda mas que el plazo general igual llega.
    monkeypatch.setattr(settings, "ASISTENTE_IA_PRIMER_FRAGMENTO_SEG", 0.05)

    async def manejador(request: httpx.Request):
        await asyncio.sleep(0.2)
        return httpx.Response(200, content=_sse({"choices": [{"delta": {"content": "Hola"}}]}))

    http = httpx.AsyncClient(transport=httpx.MockTransport(manejador))
    cadena = CadenaProveedores([Proveedor("ollama", "http://ollama.test", "ollama", "m", {}, 5.0)])
    assert ("texto", "Hola") in _recolectar(cadena, http)
