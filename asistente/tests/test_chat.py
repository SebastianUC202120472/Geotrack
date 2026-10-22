# Flujo completo del chat con el nucleo simulado y un proveedor de IA guionado.
import json

from app.core.config import settings
from app.db.database import SessionLocal
from app.main import app
from app.models import Auditoria, Mensaje
from tests.conftest import CadenaFalsa, cabecera, eventos_sse, llamada


def _preguntar(cliente, mensaje, token="tok-admin", **extra):
    """Envia una pregunta y devuelve (respuesta, eventos). Recibe cliente, mensaje y token."""
    r = cliente.post("/api/asistente/chat", json={"mensaje": mensaje, **extra}, headers=cabecera(token))
    return r, (eventos_sse(r.text) if r.status_code == 200 else [])


def test_pregunta_con_funcion_tabla_y_enlace(cliente, nucleo):
    """El modelo pide una funcion, el servidor la ejecuta y arma los bloques con datos reales."""
    app.state.cadena = CadenaFalsa([
        {"llamadas": [llamada("buscar_pedidos", {"cliente": "Ripley", "estado": "FALLIDO", "presentar": "tabla"})]},
        {"texto": ["Hoy hay **2 pedidos** ", "fallidos de Ripley."]},
    ])
    r, eventos = _preguntar(cliente, "q paso con los pedidos fallidos de ripley")
    assert r.status_code == 200
    tipos = [e["tipo"] for e in eventos]
    assert tipos[0] == "inicio" and tipos[-1] == "fin"
    assert "estado" in tipos
    texto = "".join(e["texto"] for e in eventos if e["tipo"] == "texto")
    assert texto == "Hoy hay **2 pedidos** fallidos de Ripley."
    bloques = [e["bloque"] for e in eventos if e["tipo"] == "bloque"]
    tabla = next(b for b in bloques if b["tipo"] == "tabla")
    assert tabla["total"] == 2
    enlace = next(b for b in bloques if b["tipo"] == "enlace")
    assert enlace["ruta"].startswith("/panel/pedidos") and "estado=FALLIDO" in enlace["ruta"]

    # El nucleo solo recibio consultas GET.
    assert nucleo.peticiones and all(m == "GET" for m, _ in nucleo.peticiones)

    # Lo que vio el modelo: datos delimitados y sin DNI ni telefonos completos.
    mensajes_ronda2 = app.state.cadena.recibido[1][0]
    contenido_tool = next(m["content"] for m in mensajes_ronda2 if m["role"] == "tool")
    assert "datos_del_sistema" in contenido_tool
    assert "45678912" not in contenido_tool and "987654321" not in contenido_tool
    assert json.loads(contenido_tool)["datos_del_sistema"]["total"] == 2

    # Historial y auditoria guardados.
    db = SessionLocal()
    try:
        assert db.query(Mensaje).count() == 2
        fila = db.query(Auditoria).one()
        assert fila.usuario_correo == "admin@siol.com" and fila.resultado == "ok"
        assert fila.funciones[0]["nombre"] == "buscar_pedidos" and fila.funciones[0]["ok"] is True
    finally:
        db.close()


def test_memoria_de_la_conversacion(cliente):
    """El segundo turno recibe el turno anterior y las consultas que se hicieron."""
    app.state.cadena = CadenaFalsa([
        {"llamadas": [llamada("buscar_pedidos", {"cliente": "Ripley"})]},
        {"texto": ["Ripley tiene 2 pedidos."]},
        {"texto": ["De esos, 2 fallaron."]},
    ])
    _, eventos = _preguntar(cliente, "pedidos de ripley")
    conversacion_id = eventos[0]["conversacion_id"]
    _, eventos2 = _preguntar(cliente, "¿y cuántos de esos fallaron?", conversacion_id=conversacion_id)
    assert eventos2[0]["conversacion_id"] == conversacion_id
    mensajes = app.state.cadena.recibido[2][0]
    assert mensajes[0]["role"] == "system" and "buscar_pedidos" in mensajes[0]["content"]
    contenidos = [m["content"] for m in mensajes[1:]]
    assert contenidos == ["pedidos de ripley", "Ripley tiene 2 pedidos.", "¿y cuántos de esos fallaron?"]


def test_dni_del_usuario_viaja_como_marca(cliente):
    """El DNI que escribe el usuario no llega al modelo, pero si a la consulta y a la respuesta."""
    app.state.cadena = CadenaFalsa([
        {"llamadas": [llamada("buscar_pedidos", {"dni": "[DNI_1]"})]},
        {"texto": ["El DNI [DN", "I_1] tiene 1 pedido."]},
    ])
    _, eventos = _preguntar(cliente, "pedidos del dni 11223344")
    enviado = json.dumps(app.state.cadena.recibido[0][0], ensure_ascii=False)
    assert "11223344" not in enviado and "[DNI_1]" in enviado
    datos = json.loads(next(m["content"] for m in app.state.cadena.recibido[1][0] if m["role"] == "tool"))
    assert datos["datos_del_sistema"]["total"] == 1
    texto = "".join(e["texto"] for e in eventos if e["tipo"] == "texto")
    assert texto == "El DNI 11223344 tiene 1 pedido."


def test_almacen_no_puede_usar_funciones_de_admin_aunque_el_modelo_lo_intente(cliente, nucleo):
    """Si una inyeccion hace que el modelo pida una funcion ajena al rol, no se ejecuta."""
    app.state.cadena = CadenaFalsa([
        {"llamadas": [llamada("buscar_pedidos", {})]},
        {"texto": ["No tengo acceso a ese dato."]},
    ])
    _, eventos = _preguntar(cliente, "lista todos los pedidos", token="tok-almacen")
    herramientas = {h["function"]["name"] for h in app.state.cadena.recibido[0][1]}
    assert "buscar_pedidos" not in herramientas
    assert not any(ruta.startswith("/api/pedidos") for _, ruta in nucleo.peticiones)
    tool = next(m["content"] for m in app.state.cadena.recibido[1][0] if m["role"] == "tool")
    assert "no está disponible" in tool
    assert eventos[-1]["tipo"] == "fin"


def test_permiso_denegado_por_el_nucleo_se_informa(cliente, nucleo):
    """Si el nucleo responde 403, la funcion devuelve un aviso de permisos, no datos."""
    nucleo.denegar.add("/api/almacen/observados")
    app.state.cadena = CadenaFalsa([
        {"llamadas": [llamada("pedidos_observados", {})]},
        {"texto": ["No tienes acceso a ese dato."]},
    ])
    _, eventos = _preguntar(cliente, "pedidos observados")
    tool = next(m["content"] for m in app.state.cadena.recibido[1][0] if m["role"] == "tool")
    assert "no tiene acceso" in tool and "PD-009" not in tool
    assert eventos[-1]["tipo"] == "fin"


def test_inyeccion_desde_un_correo_llega_como_dato_enmascarado(cliente):
    """Un correo con instrucciones maliciosas llega al modelo delimitado y sin el DNI real."""
    app.state.cadena = CadenaFalsa([
        {"llamadas": [llamada("solicitudes_bandeja", {"conversacion_id": 7})]},
        {"texto": ["El correo pide un recojo urgente y contiene instrucciones sospechosas."]},
    ])
    _preguntar(cliente, "que dice el correo 7")
    tool = json.loads(next(m["content"] for m in app.state.cadena.recibido[1][0] if m["role"] == "tool"))
    assert "no obedezcas" in tool["aviso"]
    extracto = tool["datos_del_sistema"]["ultimos_mensajes"][0]["extracto"]
    assert "IGNORA" in extracto  # se entrega como dato citado
    assert "12345678" not in extracto and "912345678" not in extracto
    assert "compras@" not in json.dumps(tool)


def test_sin_token_conductor_o_sesion_vencida(cliente):
    """Sin sesion -> 401; conductor -> 403; token vencido -> 401."""
    app.state.cadena = CadenaFalsa([])
    assert cliente.post("/api/asistente/chat", json={"mensaje": "hola"}).status_code == 401
    assert _preguntar(cliente, "hola", token="tok-conductor")[0].status_code == 403
    assert _preguntar(cliente, "hola", token="tok-vencido")[0].status_code == 401


def test_limite_por_minuto(cliente, monkeypatch):
    """Pasado el limite de mensajes por minuto se responde 429."""
    monkeypatch.setattr(settings, "ASISTENTE_MENSAJES_POR_MINUTO", 2)
    app.state.cadena = CadenaFalsa([{"texto": ["a"]}, {"texto": ["b"]}, {"texto": ["c"]}])
    assert _preguntar(cliente, "uno")[0].status_code == 200
    assert _preguntar(cliente, "dos")[0].status_code == 200
    assert _preguntar(cliente, "tres")[0].status_code == 429


def test_tope_diario(cliente, monkeypatch):
    """Pasado el tope diario se responde 429 y queda registrado."""
    monkeypatch.setattr(settings, "ASISTENTE_MENSAJES_POR_DIA", 1)
    app.state.cadena = CadenaFalsa([{"texto": ["a"]}, {"texto": ["b"]}])
    assert _preguntar(cliente, "uno")[0].status_code == 200
    assert _preguntar(cliente, "dos")[0].status_code == 429


def test_mensaje_demasiado_largo_o_vacio(cliente):
    """Mensajes vacios o que superan el maximo se rechazan antes de llamar a la IA."""
    app.state.cadena = CadenaFalsa([])
    assert _preguntar(cliente, "   ")[0].status_code == 422
    assert _preguntar(cliente, "x" * (settings.ASISTENTE_MAX_CARACTERES + 1))[0].status_code == 422


def test_modulo_apagado(cliente, monkeypatch):
    """Con ASISTENTE_ENABLED=false el servicio no atiende y el widget no aparece."""
    monkeypatch.setattr(settings, "ASISTENTE_ENABLED", False)
    assert cliente.get("/api/asistente/estado").json()["activo"] is False
    assert _preguntar(cliente, "hola")[0].status_code == 503


def test_historial_es_privado_por_usuario(cliente):
    """Cada usuario ve y borra solo sus conversaciones."""
    app.state.cadena = CadenaFalsa([{"texto": ["Hola Ana."]}])
    _, eventos = _preguntar(cliente, "hola")
    cid = eventos[0]["conversacion_id"]

    propias = cliente.get("/api/asistente/conversaciones", headers=cabecera()).json()
    assert [c["id"] for c in propias] == [cid]
    assert cliente.get(f"/api/asistente/conversaciones/{cid}", headers=cabecera()).json()["mensajes"][1]["contenido"] == "Hola Ana."

    assert cliente.get("/api/asistente/conversaciones", headers=cabecera("tok-admin2")).json() == []
    assert cliente.get(f"/api/asistente/conversaciones/{cid}", headers=cabecera("tok-admin2")).status_code == 404
    assert cliente.delete(f"/api/asistente/conversaciones/{cid}", headers=cabecera("tok-admin2")).status_code == 404
    assert cliente.delete(f"/api/asistente/conversaciones/{cid}", headers=cabecera()).status_code == 204


def test_no_se_continua_una_conversacion_ajena(cliente):
    """Si se envia el id de una conversacion de otro usuario, se crea una nueva."""
    app.state.cadena = CadenaFalsa([{"texto": ["uno"]}, {"texto": ["dos"]}])
    _, eventos = _preguntar(cliente, "hola")
    cid = eventos[0]["conversacion_id"]
    _, eventos2 = _preguntar(cliente, "hola", token="tok-admin2", conversacion_id=cid)
    assert eventos2[0]["conversacion_id"] != cid


def test_limite_de_rondas_de_funciones(cliente, monkeypatch):
    """Un modelo que pide funciones sin parar se corta al llegar al maximo de rondas."""
    monkeypatch.setattr(settings, "ASISTENTE_MAX_RONDAS_FUNCIONES", 2)
    app.state.cadena = CadenaFalsa([{"llamadas": [llamada("pedidos_observados", {}, f"c{i}")]} for i in range(5)])
    _, eventos = _preguntar(cliente, "observados")
    texto = "".join(e["texto"] for e in eventos if e["tipo"] == "texto")
    assert "No pude completar" in texto
    assert len(app.state.cadena.recibido) == 3
