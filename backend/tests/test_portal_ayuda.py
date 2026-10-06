from types import SimpleNamespace

from app.services.portal_service import _fila_ayuda, seleccionar_pedidos_ayuda


def _pedido(codigo, estado, dni="45873216", ref="SGF-DEMO-01"):
    return SimpleNamespace(cliente_origen="Saga Falabella S.A.", codigo=codigo, referencia_externa=ref,
                           estado=estado, dni_destinatario=dni)


def test_fila_ayuda_muestra_estado_del_portal_y_ultimos_4_del_dni():
    fila = _fila_ayuda(_pedido("PD-001", "ASIGNADO"), None)
    assert fila == {"retail": "Saga Falabella S.A.", "codigo": "PD-001", "referencia": "SGF-DEMO-01",
                    "estado": "Por salir", "dni": "3216"}


def test_fila_ayuda_usa_el_detalle_terminal_de_la_ruta():
    """Una parada FALLIDA se ve 'Reprogramado' aunque el pedido ya volvio a la cola."""
    det = SimpleNamespace(estado_entrega="FALLIDO")
    assert _fila_ayuda(_pedido("PD-003", "LISTO_PARA_ENVIO"), det)["estado"] == "Reprogramado"
    assert _fila_ayuda(_pedido("PD-006", "OBSERVADO"), None)["estado"] == "En gestión"


def test_si_caben_se_muestran_todos_los_pedidos():
    filas = [_fila_ayuda(_pedido(f"PD-00{i}", "ENTREGADO"), None) for i in range(1, 7)]
    assert seleccionar_pedidos_ayuda(filas) == filas


def test_si_son_muchos_se_muestra_uno_por_tienda_y_estado():
    filas = [_fila_ayuda(_pedido(f"PD-{i:03}", "ENTREGADO" if i % 2 else "EN_RUTA"), None) for i in range(1, 30)]
    elegidos = seleccionar_pedidos_ayuda(filas)
    assert [f["estado"] for f in elegidos] == ["Entregado", "En camino"]
