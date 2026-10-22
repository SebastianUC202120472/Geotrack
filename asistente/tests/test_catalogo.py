# Lista cerrada de funciones: solo lectura, validada y filtrada por rol.
import inspect

import pytest

from app.herramientas import cliente_core
from app.herramientas.catalogo import (
    DEFINICIONES,
    ETIQUETAS,
    ArgumentoInvalido,
    herramientas_para_rol,
    nombres_para_rol,
    validar_argumentos,
)
from app.herramientas.cliente_core import ClienteCore, ruta_permitida
from app.herramientas.funciones import FUNCIONES


def test_entre_8_y_12_funciones_y_todas_implementadas():
    """Cada funcion declarada tiene implementacion y etiqueta."""
    assert 8 <= len(DEFINICIONES) <= 12
    assert set(DEFINICIONES) == set(FUNCIONES) == set(ETIQUETAS)


def test_almacen_no_recibe_funciones_de_administrador():
    """Un usuario de almacen solo ve las funciones de datos que su rol ve en el panel."""
    almacen = set(nombres_para_rol("almacen"))
    assert "buscar_pedidos" not in almacen
    assert "solicitudes_bandeja" not in almacen
    assert {"retornos_almacen", "pedidos_observados", "ubicacion_conductores"} <= almacen
    assert nombres_para_rol("conductor") == []


def test_formato_tools_compatible():
    """Las definiciones salen en formato 'tools' compatible con OpenAI."""
    for h in herramientas_para_rol("admin"):
        assert h["type"] == "function"
        assert h["function"]["parameters"]["type"] == "object"


def test_esquema_compacto_para_el_modelo_sin_perder_validacion():
    """Al modelo no se le mandan las reglas que valida el servidor ni la descripcion repetida de
    'presentar', pero el validador las sigue aplicando."""
    import json

    import pytest

    from app.herramientas.catalogo import ArgumentoInvalido, DEFINICIONES

    enviado = json.dumps(herramientas_para_rol("admin"), ensure_ascii=False)
    assert "maxLength" not in enviado and "pattern" not in enviado and "minimum" not in enviado
    assert "Cómo mostrar el resultado" not in enviado
    buscar = next(h["function"] for h in herramientas_para_rol("admin") if h["function"]["name"] == "buscar_pedidos")
    assert set(buscar["parameters"]["properties"]) == set(DEFINICIONES["buscar_pedidos"]["parametros"])
    with pytest.raises(ArgumentoInvalido):
        validar_argumentos("buscar_pedidos", {"desde": "22/10/2026"})
    with pytest.raises(ArgumentoInvalido):
        validar_argumentos("retornos_almacen", {"ruta_id": 0})
    assert len(validar_argumentos("buscar_pedidos", {"cliente": "x" * 200})["cliente"]) == 80


def test_almacen_solo_recibe_sus_funciones():
    """Cada rol recibe solo sus funciones: almacen no carga las de admin (menos tokens y menos riesgo)."""
    nombres = {h["function"]["name"] for h in herramientas_para_rol("almacen")}
    assert "buscar_pedidos" not in nombres and "solicitudes_bandeja" not in nombres
    assert len(nombres) < len(herramientas_para_rol("admin"))


def test_validacion_descarta_claves_desconocidas_y_normaliza():
    """Claves extra (p. ej. 'sql') se ignoran y los enum se normalizan."""
    args = validar_argumentos("buscar_pedidos", {"estado": "fallido", "sql": "DROP TABLE pedidos", "presentar": "Gráfico"})
    assert args == {"estado": "FALLIDO", "presentar": "grafico"}


@pytest.mark.parametrize("argumentos", [
    {"estado": "BORRADO"},
    {"desde": "22/10/2026"},
    {"desde": "2026-13-40"},
    {"codigo": {"$ne": 1}},
])
def test_validacion_rechaza_argumentos_invalidos(argumentos):
    """Estados inexistentes, fechas mal formadas u objetos se rechazan."""
    with pytest.raises(ArgumentoInvalido):
        validar_argumentos("buscar_pedidos", argumentos)


def test_requeridos():
    """La trazabilidad exige el codigo."""
    with pytest.raises(ArgumentoInvalido):
        validar_argumentos("trazabilidad_pedido", {})


@pytest.mark.parametrize("ruta", [
    "/pedidos/1/cancelar",
    "/pedidos/1/reprogramar",
    "/rutas/asignar-bloque",
    "/usuarios/",
    "/dashboard/pedidos/../usuarios/historial",
    "/dashboard/pedidos/PD-1/historial?x=1",
    "/correos/sincronizar",
    "http://evil.com/x",
])
def test_rutas_fuera_de_la_lista_cerrada(ruta):
    """El cliente del nucleo rechaza cualquier ruta que no sea de consulta."""
    assert not ruta_permitida(ruta)


def test_cliente_core_solo_tiene_get():
    """El cliente del nucleo no expone metodos que escriban."""
    metodos = {n for n, _ in inspect.getmembers(ClienteCore, inspect.isfunction) if not n.startswith("_")}
    assert metodos == {"get"}
    fuente = inspect.getsource(cliente_core)
    for verbo in (".post(", ".put(", ".patch(", ".delete("):
        assert verbo not in fuente
