import sys
from pathlib import Path

# scripts/ no es un paquete instalable: se agrega al path como hace el propio script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from datos_demo_portal import (  # noqa: E402
    EMPRESAS, DISTRITOS, DISTRITOS_PENDIENTES, reparto_estados, destinatario, direccion,
)


def test_hay_cinco_empresas_con_credenciales_unicas():
    assert len(EMPRESAS) == 5
    assert len(set(e["codigo_acceso"] for e in EMPRESAS)) == 5
    assert len(set(e["ruc"] for e in EMPRESAS)) == 5
    assert len(set(e["prefijo_ref"] for e in EMPRESAS)) == 5
    for e in EMPRESAS:
        assert e["clave"] and e["correo_portal"] and e["direccion_origen"]


def test_el_reparto_suma_el_total_y_respeta_las_cuotas():
    r = reparto_estados(50)
    assert len(r) == 50
    assert r.count("ENTREGADO") == 30
    assert r.count("EN_RUTA") == 6
    assert r.count("LISTO_PARA_ENVIO") == 8
    assert r.count("FALLIDO") == 3
    assert r.count("OBSERVADO") == 3


def test_los_distritos_pendientes_estan_en_el_catalogo():
    """Los pedidos sin asignar se concentran en pocas zonas para que la ruta en vivo tenga paradas."""
    assert 2 <= len(DISTRITOS_PENDIENTES) <= 3
    for d in DISTRITOS_PENDIENTES:
        assert d in DISTRITOS


def test_cada_distrito_tiene_coordenadas_de_lima():
    for nombre, (lat, lng) in DISTRITOS.items():
        assert -12.4 < lat < -11.8, nombre
        assert -77.2 < lng < -76.8, nombre


def test_los_destinatarios_tienen_dni_de_ocho_digitos_y_no_se_repiten():
    dnis = {destinatario(i)["dni"] for i in range(250)}
    assert len(dnis) == 250
    for d in dnis:
        assert len(d) == 8 and d.isdigit()


def test_la_direccion_deja_el_distrito_en_la_segunda_posicion():
    """El backend saca el distrito del texto tras la primera coma; el formato debe respetarlo."""
    texto = direccion(7, "Miraflores")
    assert texto.split(",")[1].strip() == "Miraflores"
    assert texto.endswith("Lima, Peru")
