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
