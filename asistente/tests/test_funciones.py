# Funciones de consulta contra el nucleo simulado.
import asyncio

import httpx

from app.core.fechas import ahora_local
from app.herramientas import funciones as F
from app.herramientas.bloques import enlace
from app.herramientas.cliente_core import ClienteCore
from app.herramientas.zonas import zona_aproximada
from tests.conftest import NucleoFalso, _pedido


def _contexto(nucleo, token="tok-admin", rol="admin"):
    """Contexto de funciones con el nucleo simulado. Recibe nucleo, token y rol."""
    http = httpx.AsyncClient(transport=httpx.MockTransport(nucleo))
    return F.Contexto(core=ClienteCore(token, http), rol=rol)


def test_buscar_por_distrito_sin_tildes_y_agrupado():
    """'miraflores' encuentra 'Miraflores' y se agrupa por estado con grafico."""
    nucleo = NucleoFalso()
    r = asyncio.run(F.buscar_pedidos(_contexto(nucleo), {"distrito": "miraflores", "agrupar_por": "estado", "presentar": "grafico"}))
    assert r.datos["total"] == 3
    assert r.datos["agrupacion"]["valores"] == {"FALLIDO": 2, "ENTREGADO": 1}
    grafico = next(b for b in r.bloques if b["tipo"] == "grafico")
    assert {d["etiqueta"]: d["valor"] for d in grafico["datos"]} == {"FALLIDO": 2, "ENTREGADO": 1}
    enlace_ = next(b for b in r.bloques if b["tipo"] == "enlace")
    assert "distrito=Miraflores" in enlace_["ruta"]


def test_buscar_por_rango_de_fechas_en_hora_de_lima():
    """Un pedido creado a las 03:00 UTC cuenta para el dia anterior en Lima."""
    nucleo = NucleoFalso()
    nucleo.pedidos = [_pedido(1, fecha_creacion="2026-10-22T03:00:00"), _pedido(2, fecha_creacion="2026-10-22T15:00:00")]
    r = asyncio.run(F.buscar_pedidos(_contexto(nucleo), {"desde": "2026-10-22", "hasta": "2026-10-22"}))
    assert r.datos["total"] == 1 and r.datos["muestra"][0]["codigo"] == "PD-002"


def test_filtros_opcionales_se_envian_anulables():
    """Al modelo se le declaran los filtros opcionales como anulables (gpt-oss manda null) y el
    validador los ignora; el esquema interno no cambia."""
    from app.herramientas.catalogo import DEFINICIONES, herramientas_para_rol, validar_argumentos
    recojos = next(h["function"] for h in herramientas_para_rol("admin") if h["function"]["name"] == "recojos_almacen")
    props = recojos["parameters"]["properties"]
    assert props["cliente"]["type"] == ["string", "null"]
    assert props["presentar"]["enum"][-1] is None
    assert DEFINICIONES["recojos_almacen"]["parametros"]["cliente"]["type"] == "string"
    assert validar_argumentos("recojos_almacen", {"cliente": None, "estado": None, "presentar": None}) == {}


def test_conductor_en_ruta_sin_gps_no_figura_con_ubicacion():
    """Un conductor con ruta cuya app nunca envio su posicion va a 'sin ubicacion' y no cuenta como en linea."""
    nucleo = NucleoFalso()
    original = nucleo._responder

    def responder(ruta, request):
        if ruta == "/api/dashboard/flota/ubicaciones":
            return httpx.Response(200, json=[{
                "conductor_id": 3, "conductor": "Rosa Medina", "ruta": "Ruta tarde Pueblo Libre",
                "latitud": None, "longitud": None, "actualizado_en": None, "en_linea": False, "pausado": False,
                "paradas": [{"latitud": -12.07, "longitud": -77.06, "destinatario": "Pedro Vargas", "secuencia": 1, "estado": "PENDIENTE"}],
            }])
        return original(ruta, request)

    nucleo._responder = responder
    r = asyncio.run(F.ubicacion_conductores(_contexto(nucleo), {}))
    assert r.datos["conductores_con_ubicacion"] == []
    assert r.datos["en_linea_ahora"] == 0
    rosa = r.datos["conductores_sin_ubicacion"][0]
    assert rosa["conductor"] == "Rosa Medina" and "desconectado" in rosa["situacion"]
    assert rosa["paradas_pendientes"] == 1


def test_resumen_del_dia_cuenta_entregados_de_hoy():
    """Los entregados de hoy se cuentan por su fecha de entrega local."""
    nucleo = NucleoFalso()
    ahora_utc = ahora_local().astimezone(__import__("datetime").timezone.utc).replace(tzinfo=None).isoformat()
    nucleo.pedidos = [_pedido(1, estado="ENTREGADO", fecha_entrega=ahora_utc), _pedido(2, estado="ENTREGADO", fecha_entrega="2020-01-01T15:00:00")]

    original = nucleo._responder

    def responder(ruta, request):
        if ruta == "/api/dashboard/resumen":
            return httpx.Response(200, json={"total_pedidos": 2, "pedidos_por_estado": {"EN_RUTA": 4}, "total_rutas": 1, "rutas_activas": 1, "rutas_finalizadas": 0})
        if ruta == "/api/dashboard/flota":
            return httpx.Response(200, json={"total_rutas": 1, "rutas": [{"ruta_id": 1, "nombre": "Ruta Miraflores", "estado": "EN_PROGRESO", "conductor_nombre": "Juan", "total_paradas": 10, "entregadas": 5, "fallidas": 3, "pendientes": 2, "avance_porcentaje": 80.0, "fecha_creacion": ahora_utc}]})
        if ruta == "/api/incidencias":
            return httpx.Response(200, json=[{"id": 1, "ruta_id": 1, "ruta_nombre": "Ruta Miraflores", "conductor_id": 5, "conductor_nombre": "Juan", "tipo": "AVERIA_MECANICA", "estado": "ABIERTA", "creado_en": ahora_utc}])
        if ruta == "/api/reportes/":
            return httpx.Response(200, json=[])
        return original(ruta, request)

    nucleo._responder = responder
    r = asyncio.run(F.resumen_del_dia(_contexto(nucleo), {}))
    assert r.datos["entregados_hoy"] == 1
    assert r.datos["fallidos_en_rutas_del_dia"] == 3
    assert r.datos["pedidos_en_ruta_ahora"] == 4
    # Los pendientes de las rutas no se envian como otra cifra global (se repetian con "en ruta").
    assert "pendientes_en_rutas_del_dia" not in r.datos
    assert r.datos["rutas_activas"][0]["pendientes"] == 2
    assert r.datos["auxilios_abiertos"][0]["ruta"] == "Ruta Miraflores"


def test_ubicacion_con_zona_aproximada_y_sin_datos_personales():
    """'¿Dónde está Juan?' devuelve la zona aproximada y no expone DNI ni licencia."""
    nucleo = NucleoFalso()
    r = asyncio.run(F.ubicacion_conductores(_contexto(nucleo), {"nombre": "juan"}))
    juan = r.datos["conductores_con_ubicacion"][0]
    assert juan["zona_aproximada"] == "Miraflores"
    assert juan["paradas_pendientes"] == 1 and juan["proxima_parada"]["numero"] == 4
    assert "40404040" not in str(r.datos) and "Q12345678" not in str(r.datos)


def test_trazabilidad_rechaza_codigos_raros():
    """Un codigo con barras o caracteres extraños no se consulta."""
    nucleo = NucleoFalso()
    r = asyncio.run(F.trazabilidad_pedido(_contexto(nucleo), {"codigo": "../usuarios"}))
    assert "error" in r.datos and not nucleo.peticiones


def test_zonas_y_enlaces():
    """Zona aproximada fuera de Lima es None; los enlaces solo van al panel."""
    assert zona_aproximada(-13.5, -71.97) is None   # Cusco
    assert zona_aproximada(-12.0464, -77.0428) == "Lima"
    assert enlace("x", "https://evil.com") is None
    assert enlace("Ver", "/panel/pedidos", {"estado": "FALLIDO", "distrito": None})["ruta"] == "/panel/pedidos?estado=FALLIDO"


def test_pedidos_fallidos_muestran_su_motivo():
    """El listado del nucleo no trae el motivo: se lee del historial de cada fallido y va a la tabla."""
    nucleo = NucleoFalso()
    original = nucleo._responder

    def responder(ruta, request):
        if ruta == "/api/dashboard/pedidos/PD-001/historial":
            return httpx.Response(200, json={"codigo": "PD-001", "motivo_fallo": "Cliente ausente"})
        return original(ruta, request)  # PD-002 responde 404: queda "Sin motivo registrado"

    nucleo._responder = responder
    r = asyncio.run(F.buscar_pedidos(_contexto(nucleo), {"estado": "FALLIDO", "presentar": "tabla"}))
    assert r.datos["motivos_de_fallo"] == {"Cliente ausente": 1, "Sin motivo registrado": 1}
    assert r.datos["muestra"][0]["motivo_fallo"] == "Cliente ausente"
    tabla = next(b for b in r.bloques if b["tipo"] == "tabla")
    assert tabla["columnas"][-1] == "Motivo de fallo" and tabla["filas"][0][-1] == "Cliente ausente"
    # Solo se consulta el historial de los fallidos y solo con GET.
    historiales = [ruta for m, ruta in nucleo.peticiones if "historial" in ruta]
    assert sorted(historiales) == ["/api/dashboard/pedidos/PD-001/historial", "/api/dashboard/pedidos/PD-002/historial"]
    assert all(m == "GET" for m, _ in nucleo.peticiones)


def test_sin_fallidos_no_consulta_historiales():
    """Si no hay pedidos FALLIDO no se hace ninguna consulta extra."""
    nucleo = NucleoFalso()
    r = asyncio.run(F.buscar_pedidos(_contexto(nucleo), {"estado": "ENTREGADO"}))
    assert "motivos_de_fallo" not in r.datos
    assert not any("historial" in ruta for _, ruta in nucleo.peticiones)


def test_reportes_de_falla_muestran_motivo_y_detalle():
    """La tabla de reportes incluye el motivo y la descripcion que escribio el conductor."""
    nucleo = NucleoFalso()
    original = nucleo._responder

    def responder(ruta, request):
        if ruta == "/api/reportes/":
            return httpx.Response(200, json=[{
                "pedido_codigo": "PD-001", "conductor_nombre": "Juan Pérez", "motivo": "Dirección incorrecta",
                "descripcion": "El número 120 no existe", "estado": "ABIERTO", "creado_en": "2026-10-22T15:00:00",
            }])
        return original(ruta, request)

    nucleo._responder = responder
    r = asyncio.run(F.reportes_falla(_contexto(nucleo), {"presentar": "tabla"}))
    tabla = next(b for b in r.bloques if b["tipo"] == "tabla")
    assert tabla["columnas"][2:4] == ["Motivo", "Detalle"]
    assert tabla["filas"][0][2:4] == ["Dirección incorrecta", "El número 120 no existe"]


def test_periodo_explicito_sin_y_con_filtro_de_fecha():
    """Sin fechas, los datos dicen que no hay filtro (el modelo no puede decir 'hoy'); con fechas, dan el rango."""
    nucleo = NucleoFalso()
    sin = asyncio.run(F.buscar_pedidos(_contexto(nucleo), {"estado": "FALLIDO"}))
    assert sin.datos["periodo"].startswith("Sin filtro de fecha")
    assert "no digas que fallaron 'hoy'" in sin.datos["nota_fecha"]
    con = asyncio.run(F.buscar_pedidos(_contexto(nucleo), {"desde": "2026-10-20", "hasta": "2026-10-22"}))
    assert con.datos["periodo"] == "Del 20/10/2026 al 22/10/2026, según la fecha de creación del pedido."
    un_dia = asyncio.run(F.buscar_pedidos(_contexto(nucleo), {"estado": "ENTREGADO", "desde": "2026-10-22", "hasta": "2026-10-22"}))
    assert un_dia.datos["periodo"] == "El 22/10/2026, según la fecha de entrega."


def test_fallidos_con_motivo_muestran_tabla_aunque_el_modelo_pida_texto():
    """Respaldo: la lista de fallidos con su motivo va en la tabla del servidor aunque presentar sea 'texto'."""
    nucleo = NucleoFalso()
    r = asyncio.run(F.buscar_pedidos(_contexto(nucleo), {"estado": "FALLIDO", "presentar": "texto", "agrupar_por": "estado"}))
    tabla = next(b for b in r.bloques if b["tipo"] == "tabla")
    assert tabla["columnas"][-1] == "Motivo de fallo" and tabla["total"] == 2
    # Un pedido de otro estado no fuerza la tabla.
    r2 = asyncio.run(F.buscar_pedidos(_contexto(nucleo), {"estado": "ENTREGADO"}))
    assert not any(b["tipo"] == "tabla" for b in r2.bloques)


def test_conteos_por_cliente_y_distrito_cubren_todos_los_pedidos():
    """Con mas pedidos que la muestra, los conteos salen de TODOS (el modelo no debe contar la muestra)."""
    nucleo = NucleoFalso()
    nucleo.pedidos = [_pedido(i, cliente_origen="Ripley" if i % 3 else "Saga") for i in range(1, 13)]
    r = asyncio.run(F.buscar_pedidos(_contexto(nucleo), {"estado": "FALLIDO"}))
    assert len(r.datos["muestra"]) == 10
    assert r.datos["conteo_por_cliente"] == {"Ripley": 8, "Saga": 4}
    assert r.datos["conteo_por_distrito"] == {"Miraflores": 12}
    assert "no cuentes sobre ella" in r.datos["nota_muestra"]


def test_enlaces_de_almacen_segun_rol():
    """El admin no tiene las pantallas de almacen en su menu: se le abre Pedidos ya filtrado.
    El personal de almacen sigue yendo a sus pantallas."""
    nucleo = NucleoFalso()
    ruta = lambda r: next(b for b in r.bloques if b["tipo"] == "enlace")["ruta"]
    admin = _contexto(nucleo)
    almacen = _contexto(nucleo, "tok-almacen", "almacen")
    assert ruta(asyncio.run(F.pedidos_observados(admin, {}))) == "/panel/pedidos?estado=OBSERVADO"
    assert ruta(asyncio.run(F.retornos_almacen(admin, {}))) == "/panel/pedidos?estado=FALLIDO"
    assert ruta(asyncio.run(F.pedidos_observados(almacen, {}))) == "/panel/almacen/observados"
    assert ruta(asyncio.run(F.retornos_almacen(almacen, {}))) == "/panel/almacen/retornos"


def test_trazabilidad_enlaza_reportes_solo_si_hay():
    """Sin reportes del pedido, el boton abre Pedidos filtrado (no una lista de reportes vacia)."""
    nucleo = NucleoFalso()
    ruta = lambda r: next(b for b in r.bloques if b["tipo"] == "enlace")["ruta"]
    r = asyncio.run(F.trazabilidad_pedido(_contexto(nucleo), {"codigo": "PD-001"}))
    assert ruta(r) == "/panel/pedidos?estado=FALLIDO&distrito=Miraflores"
    nucleo.reportes = [{"pedido_codigo": "PD-001", "estado": "ABIERTO"}]
    r = asyncio.run(F.trazabilidad_pedido(_contexto(nucleo), {"codigo": "PD-001"}))
    assert ruta(r) == "/panel/reportes?pedido=PD-001"


def test_retornos_detalle_por_nombre_de_ruta():
    """'detalle de Ruta Miraflores' trae los codigos de sus paquetes sin que el modelo sepa el id."""
    nucleo = NucleoFalso()
    r = asyncio.run(F.retornos_almacen(_contexto(nucleo), {"ruta": "miraflores"}))
    assert [f["codigo"] for f in r.datos["fallidos"]] == ["PD-001", "PD-002"]
    tabla = next(b for b in r.bloques if b["tipo"] == "tabla")
    assert tabla["filas"][0][0] == "PD-001"
    r = asyncio.run(F.retornos_almacen(_contexto(nucleo), {"ruta": "Cusco"}))
    assert "error" in r.datos


def test_tabla_vacia_no_se_muestra():
    """Una consulta sin resultados no pinta una tabla con solo encabezados."""
    from app.herramientas.bloques import tabla
    assert tabla("Rutas", ["Ruta"], []) is None
