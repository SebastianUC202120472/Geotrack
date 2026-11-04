from app.core.config import settings
from app.services import almacen_service


def test_sin_modo_demo_solo_se_ingresa_lo_recogido(monkeypatch):
    """De fabrica, el almacen solo ingresa recojos que el conductor ya recogio."""
    monkeypatch.setattr(settings, "ALMACEN_INGRESO_DIRECTO", False)
    assert almacen_service.estados_ingresables() == ("RECOGIDO", "INGRESADO")


def test_modo_demo_permite_recibir_la_solicitud_directo(monkeypatch):
    """En modo demostracion, la solicitud recien aceptada (SOLICITADO) tambien se ingresa."""
    monkeypatch.setattr(settings, "ALMACEN_INGRESO_DIRECTO", True)
    assert "SOLICITADO" in almacen_service.estados_ingresables()
    assert "RECOGIDO" in almacen_service.estados_ingresables()
