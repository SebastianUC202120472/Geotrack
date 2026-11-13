from app.services import pedido_service


def test_zonas_por_enrutar_suma_pendientes_y_asignados_por_distrito(monkeypatch):
    """Cada distrito junta sus pendientes y asignados; las zonas salen de mayor a menor carga."""
    filas = [
        ("Miraflores", "LISTO_PARA_ENVIO", 3),
        ("Miraflores", "ASIGNADO", 1),
        ("Surco", "LISTO_PARA_ENVIO", 7),
        (None, "ASIGNADO", 2),
    ]
    monkeypatch.setattr(pedido_service.pedido_repository, "contar_activos_por_distrito", lambda db: filas)

    zonas = pedido_service.zonas_por_enrutar(db=None)["zonas"]

    assert zonas == [
        {"distrito": "Surco", "pendientes": 7, "asignados": 0},
        {"distrito": "Miraflores", "pendientes": 3, "asignados": 1},
        {"distrito": "", "pendientes": 0, "asignados": 2},
    ]


def test_zonas_por_enrutar_sin_pedidos_activos(monkeypatch):
    monkeypatch.setattr(pedido_service.pedido_repository, "contar_activos_por_distrito", lambda db: [])
    assert pedido_service.zonas_por_enrutar(db=None) == {"zonas": []}


def test_listar_pedidos_agrega_la_ultima_interaccion(monkeypatch):
    """Cada pedido trae la fecha de su último cambio; sin historial se usa la de creación."""
    from datetime import datetime
    from types import SimpleNamespace
    creado = datetime(2026, 11, 1, 9, 0)
    cambio = datetime(2026, 11, 10, 15, 30)
    pedidos = [SimpleNamespace(id=1, fecha_creacion=creado), SimpleNamespace(id=2, fecha_creacion=creado)]
    monkeypatch.setattr(pedido_service.pedido_repository, "listar", lambda db, **k: pedidos)
    monkeypatch.setattr(pedido_service.ruta_repository, "mapa_ruta_por_pedidos", lambda db, ids: {})
    monkeypatch.setattr(pedido_service.historial_repository, "ultima_fecha_por_pedidos", lambda db, ids: {1: cambio})

    resultado = pedido_service.listar_pedidos(db=None, skip=0, limit=10)

    assert [p.ultima_interaccion for p in resultado] == [cambio, creado]
