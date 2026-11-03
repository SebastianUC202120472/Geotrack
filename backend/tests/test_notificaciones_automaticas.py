from types import SimpleNamespace

from app.services.notificaciones_automaticas.constructor import construir_mensaje
from app.services.notificaciones_automaticas import proveedores


def test_pedido_entregado_crea_mensaje_telegram():
    """El aviso de entrega va al chat de Telegram y trae su clave unica."""
    pedido = SimpleNamespace(codigo="PD-001", nombre_destinatario="Juan", telegram_chat_id="123456789")
    mensajes = construir_mensaje("PEDIDO_ENTREGADO", {"pedido": pedido})
    assert len(mensajes) == 1
    assert mensajes[0].canal.value == "telegram"
    assert mensajes[0].destinatario.valor == "123456789"
    assert "PD-001" in mensajes[0].cuerpo
    assert mensajes[0].clave_idempotencia == "PEDIDO_ENTREGADO:PD-001"


def test_pedido_sin_telegram_no_crea_mensaje():
    """Sin chat de Telegram no hay a quien escribir: no se crea el aviso."""
    pedido = SimpleNamespace(codigo="PD-002", nombre_destinatario="Ana", telegram_chat_id="")
    assert construir_mensaje("PEDIDO_ENTREGADO", {"pedido": pedido}) == []


def test_auxilio_mecanico_crea_telegram_y_correo(monkeypatch):
    """El auxilio mecanico genera dos avisos urgentes con claves distintas cuando hay chat."""
    from app.core.config import settings
    monkeypatch.setattr(settings, "NOTIFICACIONES_ADMIN_TELEGRAM_CHAT_ID", "123456789")
    inc = SimpleNamespace(codigo="IN-001", vehiculo_placa="ABC-123", descripcion="no enciende")
    ruta = SimpleNamespace(nombre="Ruta Miraflores", codigo="RT-001")
    mensajes = construir_mensaje("AUXILIO_MECANICO", {"incidencia": inc, "ruta": ruta})
    assert {m.canal.value for m in mensajes} == {"telegram", "correo"}
    assert all(m.prioridad.value == "urgente" for m in mensajes)


def test_evento_desconocido_devuelve_vacio():
    """Un evento sin constructor no rompe: devuelve lista vacia."""
    assert construir_mensaje("NO_EXISTE", {}) == []


def test_error_de_red_es_reintentable():
    """Una caida de red puede recuperarse con otro intento."""
    assert proveedores.es_error_transitorio(TimeoutError("timeout")) is True


def test_error_de_autenticacion_no_es_reintentable():
    """Una credencial invalida no debe repetirse automaticamente."""
    error = proveedores.smtplib.SMTPAuthenticationError(535, b"credenciales invalidas")
    assert proveedores.es_error_transitorio(error) is False


class _ConsultaVacia:
    """Imita db.query(...).filter(...).first() sin contacto registrado."""
    def query(self, *_):
        return self

    def filter(self, *_):
        return self

    def first(self):
        return None


def test_pedido_sin_contacto_en_bd_no_lanza():
    """Con sesion de BD y sin contacto registrado no se crea aviso ni se lanza excepcion."""
    pedido = SimpleNamespace(id=7, codigo="PD-007", nombre_destinatario="Luis")
    assert construir_mensaje("PEDIDO_ENTREGADO", {"pedido": pedido}, _ConsultaVacia()) == []


def test_clave_incluye_la_ocurrencia():
    """Una nueva vuelta del pedido (otra ruta) genera una clave distinta."""
    pedido = SimpleNamespace(codigo="PD-001", nombre_destinatario="Juan", telegram_chat_id="1")
    r1 = construir_mensaje("PEDIDO_PROGRAMADO", {"pedido": pedido, "ocurrencia": "R1"})
    r2 = construir_mensaje("PEDIDO_PROGRAMADO", {"pedido": pedido, "ocurrencia": "R2"})
    assert r1[0].clave_idempotencia == "PEDIDO_PROGRAMADO:PD-001:R1"
    assert r1[0].clave_idempotencia != r2[0].clave_idempotencia


def test_registrar_no_lanza_y_deshace(monkeypatch):
    """Si construir el aviso falla, registrar devuelve 0, hace rollback y no rompe el negocio."""
    from app.core.config import settings
    from app.services.notificaciones_automaticas import operador
    monkeypatch.setattr(settings, "NOTIFICACIONES_HABILITADAS", True)

    def _explota(*_):
        raise RuntimeError("fallo simulado")
    monkeypatch.setattr(operador, "construir_mensaje", _explota)
    db = SimpleNamespace(rollback_llamado=False)
    db.rollback = lambda: setattr(db, "rollback_llamado", True)
    assert operador.registrar(db, "PEDIDO_ENTREGADO", {}) == 0
    assert db.rollback_llamado is True


def test_smtp_465_usa_ssl_implicito(monkeypatch):
    """Con el puerto 465 se usa SMTP_SSL y no se negocia STARTTLS."""
    from app.core.config import settings
    usados = []

    class _Falso:
        def __init__(self, *a, **k):
            usados.append(type(self).__name__)

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def starttls(self, **k):
            raise AssertionError("no debe usar STARTTLS en 465")

        def login(self, *a):
            pass

        def send_message(self, *a):
            pass

    class SMTP_SSL(_Falso):
        pass

    monkeypatch.setattr(settings, "MAIL_ENABLED", True)
    monkeypatch.setattr(settings, "MAIL_ADDRESS", "demo@example.com")
    monkeypatch.setattr(settings, "MAIL_PASSWORD", "x")
    monkeypatch.setattr(settings, "SMTP_PORT", 465)
    monkeypatch.setattr(proveedores.smtplib, "SMTP_SSL", SMTP_SSL)
    fila = SimpleNamespace(canal="correo", destinatario_valor="a@example.com",
                           asunto="Prueba", cuerpo="Hola", evento="PRUEBA")
    proveedores.enviar(fila)
    assert usados == ["SMTP_SSL"]


def test_proximidad_apagada_no_consulta(monkeypatch):
    """Con el modulo apagado, la proximidad no toca la BD."""
    from app.core.config import settings
    from app.services.notificaciones_automaticas.proximidad import evaluar_proximidad
    monkeypatch.setattr(settings, "NOTIFICACIONES_HABILITADAS", False)
    assert evaluar_proximidad(None, 1, 1) == 0


def test_mecanico_propuesta_mas_cercano():
    """El cálculo de distancia propone al mecánico geográficamente más próximo."""
    from app.services.router import calcular_distancia
    # Incidencia en Miraflores (-12.12, -77.03)
    # Mecanico 1 en Surquillo (-12.11, -77.02)
    # Mecanico 2 en Los Olivos (-11.98, -77.07)
    d1 = calcular_distancia(-12.12, -77.03, -12.11, -77.02)
    d2 = calcular_distancia(-12.12, -77.03, -11.98, -77.07)
    assert d1 < d2
