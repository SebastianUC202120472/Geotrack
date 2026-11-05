# Pruebas de seguridad y configuracion del centro de notificaciones (sin base de datos).
import hashlib
import hmac
import json
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.services.notificaciones_automaticas import administracion, constructor, vinculos, webhooks
from app.services.notificaciones_automaticas.constructor import _rellenar, _variables, construir_mensaje


# --- Token de vinculacion de Telegram ---

def test_token_de_vinculo_valido_se_lee():
    """Un token recien creado devuelve el tipo y el id de la entidad."""
    token = vinculos.crear_token("pedido", 42, ahora=1_800_000_000)
    assert vinculos.leer_token(token, ahora=1_800_000_100) == ("pedido", 42)
    assert len(token) <= 64 and all(c.isalnum() or c in "_-" for c in token)


def test_token_alterado_o_vencido_se_rechaza():
    """Cambiar el id, la firma o usarlo vencido invalida el token."""
    token = vinculos.crear_token("pedido", 42, ahora=1_800_000_000)
    assert vinculos.leer_token(token.replace("P42_", "P43_"), ahora=1_800_000_100) is None
    assert vinculos.leer_token(token[:-1] + ("A" if token[-1] != "A" else "B"), ahora=1_800_000_100) is None
    assert vinculos.leer_token(token, ahora=1_800_000_000 + vinculos.VIGENCIA_SEG + 1) is None


def test_el_codigo_viejo_pd_ya_no_vincula():
    """El formato anterior "PD_PD-001" (adivinable) no se acepta."""
    assert vinculos.leer_token("PD_PD-001") is None


def test_enlace_solo_con_bot_configurado(monkeypatch):
    """Sin bot o con el modulo apagado no se entrega enlace."""
    monkeypatch.setattr(settings, "NOTIFICACIONES_HABILITADAS", True)
    monkeypatch.setattr(settings, "TELEGRAM_BOT_TOKEN", "x")
    monkeypatch.setattr(settings, "TELEGRAM_BOT_USERNAME", "")
    assert vinculos.enlace_telegram("pedido", 1) is None
    monkeypatch.setattr(settings, "TELEGRAM_BOT_USERNAME", "@MiBot")
    assert vinculos.enlace_telegram("pedido", 1).startswith("https://t.me/MiBot?start=P1_")


# --- Verificacion de webhooks ---

def test_telegram_exige_el_secreto(monkeypatch):
    """Sin secreto configurado o con uno distinto, la llamada no se acepta."""
    monkeypatch.setattr(settings, "TELEGRAM_WEBHOOK_SECRET", "")
    assert not webhooks.verificar_telegram("cualquiera")
    monkeypatch.setattr(settings, "TELEGRAM_WEBHOOK_SECRET", "s3creto")
    assert not webhooks.verificar_telegram(None)
    assert not webhooks.verificar_telegram("otro")
    assert webhooks.verificar_telegram("s3creto")


def test_whatsapp_exige_la_firma(monkeypatch):
    """La firma debe ser el HMAC-SHA256 del cuerpo exacto con el app secret."""
    cuerpo = b'{"entry": []}'
    monkeypatch.setattr(settings, "WHATSAPP_APP_SECRET", "")
    assert not webhooks.verificar_firma_whatsapp(cuerpo, "sha256=abc")
    monkeypatch.setattr(settings, "WHATSAPP_APP_SECRET", "app-secret")
    firma = "sha256=" + hmac.new(b"app-secret", cuerpo, hashlib.sha256).hexdigest()
    assert webhooks.verificar_firma_whatsapp(cuerpo, firma)
    assert not webhooks.verificar_firma_whatsapp(cuerpo + b" ", firma)
    assert not webhooks.verificar_firma_whatsapp(cuerpo, None)


def test_handshake_sin_token_configurado_se_rechaza(monkeypatch):
    """El handshake de Meta no tiene valor por defecto: vacio = rechazo."""
    monkeypatch.setattr(settings, "WHATSAPP_VERIFY_TOKEN", "")
    assert not webhooks.verificar_handshake("subscribe", "")
    monkeypatch.setattr(settings, "WHATSAPP_VERIFY_TOKEN", "tok")
    assert webhooks.verificar_handshake("subscribe", "tok")
    assert not webhooks.verificar_handshake("subscribe", "otro")


def test_webhooks_sin_firma_responden_403(monkeypatch):
    """Por HTTP, un webhook sin credenciales del proveedor se rechaza antes de procesar nada."""
    monkeypatch.setattr(settings, "TELEGRAM_WEBHOOK_SECRET", "s3creto")
    monkeypatch.setattr(settings, "WHATSAPP_APP_SECRET", "app-secret")
    cliente = TestClient(app)
    falso_start = {"message": {"text": "/start PD_PD-001", "chat": {"id": 1}}}
    assert cliente.post("/api/notificaciones/webhook/telegram", json=falso_start).status_code == 403
    stop = {"entry": [{"changes": [{"value": {"messages": [{"from": "51987654321", "text": {"body": "STOP"}}]}}]}]}
    assert cliente.post("/api/notificaciones/webhook/whatsapp", json=stop).status_code == 403
    assert cliente.get("/api/notificaciones/webhook/whatsapp",
                       params={"hub.mode": "subscribe", "hub.verify_token": "geotrack_webhook_secret"}).status_code == 403


def test_boton_voy_de_otro_chat_se_ignora(monkeypatch):
    """Un VOY de un chat que no es el mecanico asignado no hace nada."""
    monkeypatch.setattr(webhooks.repo, "obtener_mecanico_por_chat", lambda db, chat: SimpleNamespace(id=9))
    llamado = []
    monkeypatch.setattr(webhooks, "_ayuda_en_camino", lambda *a: llamado.append(a))
    res = webhooks.procesar_telegram(None, {"callback_query": {"data": "VOY:AYUDA_ASIGNADA:IN-001:5", "from": {"id": 777}}})
    assert res["accion"] == "IGNORADA" and not llamado


# --- Plantillas y bajas al armar los avisos ---

def test_rellenar_no_permite_leer_atributos():
    """Solo se reemplazan nombres simples; {x.__class__} queda como texto."""
    assert _rellenar("Hola {nombre}, {nombre.__class__} {otro}", {"nombre": "Ana"}) == "Hola Ana, {nombre.__class__} {otro}"


def test_las_plantillas_de_fabrica_usan_variables_conocidas():
    """Cada variable de las plantillas de fabrica existe en el contexto de su evento."""
    pedido = SimpleNamespace(codigo="PD-1", nombre_destinatario="Ana")
    recojo = SimpleNamespace(codigo="RC-1", cliente_origen="Ripley", cantidad_declarada=3)
    inc = SimpleNamespace(codigo="IN-1", vehiculo_placa="ABC-123", descripcion="no enciende")
    contextos = {
        "PEDIDO_EN_CAMINO": {"pedido": pedido, "secuencia": 2, "total": 9},
        "PEDIDO_NO_ENTREGADO": {"pedido": pedido, "motivo": "ausente"},
        "RECOJO_COMPLETADO": {"recojo": recojo}, "PAQUETES_FALTANTES": {"recojo": recojo, "faltantes": ["PD-7"]},
        "RETORNOS_ALMACEN": {"ruta": SimpleNamespace(codigo="RT-1"), "fallidos": [pedido]},
        "AUXILIO_MECANICO": {"incidencia": inc}, "AYUDA_ASIGNADA": {"incidencia": inc, "conductor_nombre": "Juan"},
        "AYUDA_EN_CAMINO": {"incidencia": inc, "mecanico_nombre": "Taller X", "mecanico_telefono": "999"},
        "RECLAMO_NUEVO": {"reclamo": SimpleNamespace(codigo="RE-1", tipo="RECLAMO", detalle="demora")},
        "RESUMEN_DEL_DIA": {"conteos": {"entregados": 5}, "fecha": "2026-11-04"},
    }
    for evento, _canal, asunto, cuerpo in administracion.EVENTOS_DEFAULT:
        variables = _variables(evento, contextos.get(evento, {"pedido": pedido}))
        for texto in (asunto, cuerpo):
            if texto:
                assert "{" not in _rellenar(texto, variables), (evento, texto)


class _BDFalsa:
    """Sesion falsa: solo marca que hay base de datos (las consultas se reemplazan en la prueba)."""

    def query(self, *a):
        """No se usa: existe para que el constructor detecte una sesion."""
        raise AssertionError("no deberia consultar")


def _pedido_con_chat():
    """Pedido de prueba con chat de Telegram. Sin input."""
    return SimpleNamespace(id=1, codigo="PD-001", nombre_destinatario="Ana", telegram_chat_id="123")


def test_no_se_envia_a_quien_pidio_stop(monkeypatch):
    """Un chat dado de baja no recibe el aviso."""
    monkeypatch.setattr(constructor.dest, "telegram_contacto", lambda db, t, i: ("", None))
    monkeypatch.setattr(constructor.repo, "esta_de_baja", lambda db, c, v: True)
    assert construir_mensaje("PEDIDO_ENTREGADO", {"pedido": _pedido_con_chat()}, _BDFalsa()) == []


def test_plantilla_apagada_omite_el_aviso_y_la_editada_cambia_el_texto(monkeypatch):
    """La plantilla del panel manda: apagada no se envia; encendida usa su texto."""
    monkeypatch.setattr(constructor.dest, "telegram_contacto", lambda db, t, i: ("", None))
    monkeypatch.setattr(constructor.repo, "esta_de_baja", lambda db, c, v: False)
    apagada = SimpleNamespace(activo=False, cuerpo="x", asunto=None)
    monkeypatch.setattr(constructor.repo, "obtener_plantilla_evento", lambda db, e, c: apagada)
    assert construir_mensaje("PEDIDO_ENTREGADO", {"pedido": _pedido_con_chat()}, _BDFalsa()) == []
    editada = SimpleNamespace(activo=True, cuerpo="Listo {nombre}: {codigo} entregado", asunto=None)
    monkeypatch.setattr(constructor.repo, "obtener_plantilla_evento", lambda db, e, c: editada)
    [m] = construir_mensaje("PEDIDO_ENTREGADO", {"pedido": _pedido_con_chat()}, _BDFalsa())
    assert m.cuerpo == "Listo Ana: PD-001 entregado"


def test_el_portal_no_trae_bot_fijo():
    """El enlace del portal ya no apunta a un bot escrito en el codigo."""
    import inspect
    from app.api import portal
    assert "GeoTrackAvisosBot" not in inspect.getsource(portal)
    assert json.dumps(administracion.EVENTOS_DEFAULT)  # definido a nivel de modulo
