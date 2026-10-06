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
