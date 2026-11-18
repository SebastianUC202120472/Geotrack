# Hallazgos 2 y 3 de la revision del nucleo: X-Real-IP solo desde proxies de confianza y
# reprogramacion del portal con limite de peticiones, una sola solicitud y un solo aviso pendiente.
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.requests import Request

from app.core import portal_token
from app.core.config import settings
from app.core.rate_limit import _ip_cliente
from app.db.database import Base, get_db
from app.main import app
from app.models.notificacion import Notificacion
from app.services import notificaciones_service, parametro_service, portal_service

FRANJAS = ["Mañana · 9 am – 1 pm", "Tarde · 2 pm – 6 pm"]


def _request(peer: str | None, real_ip: str | None = None) -> Request:
    """Request minima con la IP del peer directo y, opcionalmente, la cabecera X-Real-IP."""
    cabeceras = [(b"x-real-ip", real_ip.encode())] if real_ip is not None else []
    return Request({"type": "http", "method": "GET", "path": "/x", "headers": cabeceras,
                    "client": (peer, 5000) if peer else None})


# ---------------- Hallazgo 2: X-Real-IP solo desde proxies de confianza ----------------

@pytest.mark.parametrize("peer,cabecera,esperada", [
    ("172.19.0.4", "200.48.1.7", "200.48.1.7"),        # Nginx o atencion en la red de Compose
    ("::ffff:172.19.0.4", "200.48.1.7", "200.48.1.7"),   # la misma IP escrita como IPv6
    ("181.65.20.9", "1.2.3.4", "181.65.20.9"),           # directo desde internet: se ignora la cabecera
    ("172.19.0.4", "no-es-ip", "172.19.0.4"),            # cabecera basura desde un proxy: cuenta el peer
    ("192.168.1.50", "1.2.3.4", "192.168.1.50"),         # la LAN no es de confianza por defecto
])
def test_x_real_ip_solo_se_acepta_desde_proxies_de_confianza(peer, cabecera, esperada):
    """Con la configuracion por defecto (172.16.0.0/12) solo la red interna de Docker puede fijar la IP."""
    assert settings.PROXIES_DE_CONFIANZA == "172.16.0.0/12"
    assert _ip_cliente(_request(peer, cabecera)) == esperada


def test_ip_falsa_en_cada_peticion_no_esquiva_el_limite():
    """Quien llega directo no puede cambiar su clave del limitador inventando una IP por peticion."""
    claves = {_ip_cliente(_request("181.65.20.9", f"10.0.0.{i}")) for i in range(20)}
    assert claves == {"181.65.20.9"}


def test_proxies_de_confianza_configurables(monkeypatch):
    """Se aceptan varias redes separadas por comas; una entrada invalida se ignora sin romper el resto."""
    monkeypatch.setattr(settings, "PROXIES_DE_CONFIANZA", " 10.10.0.0/16 , esto-no-es-red, fd00::/8 ")
    assert _ip_cliente(_request("10.10.3.3", "200.48.1.7")) == "200.48.1.7"
    assert _ip_cliente(_request("fd00::5", "200.48.1.7")) == "200.48.1.7"
    assert _ip_cliente(_request("172.19.0.4", "200.48.1.7")) == "172.19.0.4"   # ya no esta en la lista
    monkeypatch.setattr(settings, "PROXIES_DE_CONFIANZA", "")
    assert _ip_cliente(_request("172.19.0.4", "200.48.1.7")) == "172.19.0.4"   # vacio = no confia en nadie


def test_sin_peer_conocido():
    """Sin IP del peer (p. ej. un transporte raro) no se usa la cabecera."""
    assert _ip_cliente(_request(None, "200.48.1.7")) == "?"


# ---------------- Hallazgo 3: reprogramar desde el portal ----------------

def test_reprogramar_tiene_limite_de_5_por_minuto(monkeypatch):
    """La sexta solicitud del mismo cliente en un minuto se rechaza con 429 antes de llegar al servicio."""
    llamadas = []
    monkeypatch.setattr(portal_service, "registrar_reprogramacion",
                        lambda db, codigo, franja: llamadas.append(codigo) or {"ok": True})
    app.dependency_overrides[get_db] = lambda: None
    app.dependency_overrides[portal_token.requiere_token_persona] = lambda: "PD-LIMITE"
    try:
        cliente = TestClient(app)
        codigos = [cliente.post("/api/portal/pedidos/PD-LIMITE/reprogramar", json={"franja": FRANJAS[0]}).status_code
                   for _ in range(6)]
    finally:
        app.dependency_overrides.clear()
    assert codigos == [200] * 5 + [429]
    assert len(llamadas) == 5


def _preparar_servicio(monkeypatch, pendiente):
    """Prepara registrar_reprogramacion con una solicitud pendiente opcional. Devuelve (guardadas, avisos)."""
    pedido = SimpleNamespace(id=9, codigo="PD-009", estado="ASIGNADO")
    guardadas, avisos = [], []
    monkeypatch.setattr(portal_service.repo, "pedido_por_codigo", lambda db, c: pedido)
    monkeypatch.setattr(portal_service.reprogramacion_repository, "pendiente_de", lambda db, pid: pendiente)
    monkeypatch.setattr(portal_service.reprogramacion_repository, "registrar",
                        lambda db, pid, f: guardadas.append(f) or SimpleNamespace(franja=f, estado="PENDIENTE"))
    monkeypatch.setattr(parametro_service, "obtener_franjas", lambda db: FRANJAS)
    monkeypatch.setattr(notificaciones_service, "registrar_o_actualizar",
                        lambda db, tipo, titulo, msg, ruta, eid: avisos.append(msg))
    monkeypatch.setattr(notificaciones_service, "registrar",
                        lambda *a, **k: pytest.fail("no debe crear un aviso nuevo sin deduplicar"))
    return guardadas, avisos


def test_misma_franja_repetida_no_escribe_ni_avisa(monkeypatch):
    """Repetir la misma franja con una solicitud PENDIENTE no toca la base ni la campana."""
    guardadas, avisos = _preparar_servicio(monkeypatch, SimpleNamespace(franja=FRANJAS[0], estado="PENDIENTE"))
    r = portal_service.registrar_reprogramacion(SimpleNamespace(commit=lambda: None), "PD-009", FRANJAS[0])
    assert r["reprogramacion"] == {"franja": FRANJAS[0], "estado": "PENDIENTE"}
    assert guardadas == [] and avisos == []


def test_otra_franja_actualiza_la_pendiente(monkeypatch):
    """Con una PENDIENTE y otra franja se actualiza esa solicitud (el repositorio no duplica) y su aviso."""
    guardadas, avisos = _preparar_servicio(monkeypatch, SimpleNamespace(franja=FRANJAS[0], estado="PENDIENTE"))
    r = portal_service.registrar_reprogramacion(SimpleNamespace(commit=lambda: None), "PD-009", FRANJAS[1])
    assert r["reprogramacion"]["franja"] == FRANJAS[1]
    assert guardadas == [FRANJAS[1]] and avisos == [f"Pedido PD-009: pide la franja «{FRANJAS[1]}»"]


@pytest.fixture()
def bd():
    """Sesion SQLite en memoria con la tabla de notificaciones. Sin input."""
    motor = create_engine("sqlite://")
    Base.metadata.create_all(motor, tables=[Notificacion.__table__])
    sesion = sessionmaker(bind=motor)()
    yield sesion
    sesion.close()


def test_un_solo_aviso_sin_ver_por_pedido(bd):
    """Varias solicitudes del mismo pedido dejan un solo aviso sin ver, con la ultima franja; si el admin
    ya lo vio, la siguiente crea uno nuevo. Otro pedido tiene su propio aviso."""
    from datetime import datetime

    titulo = "Reprogramación solicitada por el cliente"
    for franja in FRANJAS + [FRANJAS[0]]:
        notificaciones_service.registrar_o_actualizar(bd, "reportes", titulo, f"pide «{franja}»", "/pedidos", 9)
    avisos = bd.query(Notificacion).all()
    assert len(avisos) == 1 and avisos[0].mensaje == f"pide «{FRANJAS[0]}»"

    avisos[0].visto_en = datetime.utcnow()
    bd.commit()
    notificaciones_service.registrar_o_actualizar(bd, "reportes", titulo, "pide otra", "/pedidos", 9)
    notificaciones_service.registrar_o_actualizar(bd, "reportes", titulo, "otro pedido", "/pedidos", 10)
    assert bd.query(Notificacion).count() == 3
    assert bd.query(Notificacion).filter(Notificacion.visto_en == None).count() == 2  # noqa: E711
