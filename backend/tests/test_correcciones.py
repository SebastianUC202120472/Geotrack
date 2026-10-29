# Pruebas de las correcciones del Excel de tareas (logica pura, sin base de datos).
from datetime import date, timedelta

import pytest

from app.schemas.cliente import normalizar_ruc, digito_ruc_valido, normalizar_razon_social
from app.schemas.conductor import validar_licencia, ConductorCreate
from app.services.verificacion_portal_service import segundos_de_bloqueo, ESCALONES_BLOQUEO_SEG


# --- C03-03: licencia de conducir ---

def test_licencia_se_normaliza():
    """La licencia acepta minusculas, espacios y guiones y se guarda limpia."""
    assert validar_licencia("q-1234 5678") == "Q12345678"


def test_licencia_mal_formada_se_rechaza():
    """Una licencia sin la letra inicial o con menos digitos no pasa."""
    with pytest.raises(ValueError):
        validar_licencia("12345678")


def test_alta_con_licencia_vencida_se_rechaza():
    """No se puede dar de alta a un conductor con la licencia vencida."""
    with pytest.raises(ValueError):
        ConductorCreate(correo="a@b.pe", contrasena="Clave12345!", nombre="Ana Pérez",
                        licencia_numero="Q12345678", licencia_vencimiento=date.today() - timedelta(days=2))


# --- C07-01: RUC y razon social ---

def test_ruc_valido_de_empresa_real():
    """Un RUC real de SUNAT cumple formato y digito verificador."""
    assert normalizar_ruc(" 20100128056 ") == "20100128056"
    assert digito_ruc_valido("20100128056")


def test_ruc_con_digito_errado():
    """Si se cambia el ultimo digito, el verificador ya no coincide."""
    assert not digito_ruc_valido("20100128057")


@pytest.mark.parametrize("ruc", ["2010012805", "201001280561", "30100128056", "20A00128056"])
def test_ruc_mal_formado(ruc):
    """Largo distinto de 11, prefijo invalido o letras: se rechaza."""
    with pytest.raises(ValueError):
        normalizar_ruc(ruc)


def test_razon_social_corta_se_rechaza():
    """La razon social exige al menos 3 caracteres utiles."""
    with pytest.raises(ValueError):
        normalizar_razon_social("  A ")
    assert normalizar_razon_social("  Saga   Falabella ") == "Saga Falabella"


# --- C42-01: bloqueo progresivo ---

def test_primer_bloqueo_usa_el_base():
    """El primer bloqueo dura lo de siempre (30 s DNI / 45 s OTP)."""
    assert segundos_de_bloqueo(30, 0) == 30


def test_bloqueos_seguidos_se_alargan_hasta_el_tope():
    """Cada bloqueo seguido dura mas y nunca pasa del ultimo escalon."""
    duraciones = [segundos_de_bloqueo(30, n) for n in range(8)]
    assert duraciones == sorted(duraciones)
    assert duraciones[-1] == ESCALONES_BLOQUEO_SEG[-1]


# --- F3: solicitudes de recojo ---
from fastapi import HTTPException  # noqa: E402
from app.models.solicitud_recojo import ESTADOS_GESTIONADOS  # noqa: E402
from app.schemas.recojo import PedidoManualIn, SolicitudManualCreate, NoRealizadoRequest  # noqa: E402
from app.services.recojo_service import _exigir_filas_validas  # noqa: E402


def test_pedido_manual_exige_referencia_y_direccion():
    """Un pedido escrito a mano sin referencia o sin direccion no pasa (C11-02)."""
    with pytest.raises(ValueError):
        PedidoManualIn(referencia_externa="  ", direccion_destino="Av. Larco 100, Miraflores")
    p = PedidoManualIn(referencia_externa=" SF-1 ", direccion_destino="Av.  Larco 100,  Miraflores")
    assert p.referencia_externa == "SF-1" and p.direccion_destino == "Av. Larco 100, Miraflores"


def test_solicitud_manual_sin_pedidos_se_rechaza():
    """La solicitud manual necesita al menos un pedido."""
    with pytest.raises(ValueError):
        SolicitudManualCreate(cliente_id=1, pedidos=[])


def test_reintento_con_todo_duplicado_es_409():
    """Si todas las filas ya existian, el reintento responde 409 y no crea nada (C11-01)."""
    with pytest.raises(HTTPException) as e:
        _exigir_filas_validas([], ["Fila 1: el pedido SF-1 ya está registrado (PD-001)"], duplicadas=1)
    assert e.value.status_code == 409


def test_filas_invalidas_sin_duplicados_es_400():
    """Si no hay filas validas por datos faltantes, responde 400 con el motivo."""
    with pytest.raises(HTTPException) as e:
        _exigir_filas_validas([], ["Fila 1: falta direccion_destino"], duplicadas=0)
    assert e.value.status_code == 400 and "falta direccion_destino" in e.value.detail


def test_no_realizado_cuenta_como_gestionado_y_exige_motivo():
    """Un recojo no realizado ya no esta pendiente en la ruta y requiere motivo (C12-02)."""
    assert "NO_REALIZADO" in ESTADOS_GESTIONADOS
    with pytest.raises(ValueError):
        NoRealizadoRequest(motivo=" a ")


# --- F4: geocodificacion (C16-01, C16-02, C16-03, C17-01) ---

from types import SimpleNamespace  # noqa: E402

from app.core.distritos import normalizar_distrito, distrito_desde_texto, resolver_distrito, ZONA_DESCONOCIDA  # noqa: E402
from app.services import geocoder, pedido_service  # noqa: E402


@pytest.mark.parametrize("texto, esperado", [
    ("Miraflores 15074", "Miraflores"),
    ("jesus maria", "Jesús María"),
    ("Distrito de Ate", "Ate"),
    ("Surco", "Santiago de Surco"),
    ("SJL", "San Juan de Lurigancho"),
    ("Provincia Constitucional del Callao", "Callao"),
    ("Arequipa", None),
])
def test_distrito_se_normaliza_con_la_lista_de_lima(texto, esperado):
    """Tildes, codigo postal, prefijos y abreviaturas llevan al nombre oficial; fuera de Lima, None."""
    assert normalizar_distrito(texto) == esperado


def test_distrito_desde_texto_mira_todos_los_tramos():
    """El distrito puede venir en cualquier tramo; "Lima" solo cuenta si no hay otro distrito."""
    assert distrito_desde_texto("Av. Aviación 1030, San Borja, Lima, Perú") == "San Borja"
    assert distrito_desde_texto("Urb. Las Flores Mz A Lt 5, Lima, San Juan de Lurigancho") == "San Juan de Lurigancho"
    assert distrito_desde_texto("Jr. Ucayali 200, Lima") == "Cercado de Lima"
    assert distrito_desde_texto("Av. Miraflores 300") is None


def test_resolver_distrito_prefiere_el_del_mapa():
    """Manda el distrito del geocodificador; si no hay, el del texto; si no, zona desconocida."""
    assert resolver_distrito("Surquillo", "Av. Angamos 1200, Miraflores") == "Surquillo"
    assert resolver_distrito(None, "Av. Angamos 1200, Miraflores") == "Miraflores"
    assert resolver_distrito("Cercado de Lima", "Calle 5, Breña") == "Breña"
    assert resolver_distrito(None, "Calle sin distrito 123") == ZONA_DESCONOCIDA


def test_distrito_de_google_y_de_osm():
    """Se lee el distrito de los componentes del resultado; la provincia ("Lima") no cuenta en OSM."""
    google = {"address_components": [
        {"long_name": "Provincia de Lima", "types": ["administrative_area_level_2"]},
        {"long_name": "Santiago de Surco", "types": ["locality", "political"]},
    ]}
    assert geocoder._distrito_google(google) == "Santiago de Surco"
    assert geocoder._distrito_osm({"address": {"suburb": "Lince", "city": "Lima"}}) == "Lince"
    assert geocoder._distrito_osm({"address": {"city": "Lima"}}) is None


def test_si_google_falla_se_usa_openstreetmap(monkeypatch):
    """Ante un error de Google (o sin resultados) se intenta con OpenStreetMap (C16-02)."""
    punto = geocoder.ResultadoGeo(-12.1, -77.0, "Lince", "Lince, Lima", "nominatim")

    class GoogleCaido:
        def geocode(self, *a, **k):
            raise RuntimeError("OVER_QUERY_LIMIT")

    monkeypatch.setattr(geocoder, "_google", GoogleCaido())
    monkeypatch.setattr(geocoder, "_buscar_osm", lambda texto, maximo: [punto])
    assert geocoder.buscar_coincidencias("Av. Arequipa 2000, Lince") == [punto]

    monkeypatch.setattr(geocoder, "_buscar_google", lambda texto, maximo: [])
    assert geocoder.buscar_coincidencias("Av. Arequipa 2000, Lince") == [punto]


def _preparar_reproceso(monkeypatch, pedidos, encontrados):
    """Simula repositorios y geocodificador para procesar_geocodificacion. Recibe los pedidos y
    las direcciones que el mapa si encuentra. Devuelve la lista de cambios de estado registrados."""
    cambios = []
    monkeypatch.setattr(pedido_service.pedido_repository, "obtener_sin_coordenadas", lambda db: pedidos)
    monkeypatch.setattr(pedido_service.pedido_repository, "guardar_cambios", lambda db: None)
    monkeypatch.setattr(pedido_service.geocoding_cache_repository, "obtener_muchas", lambda db, d: {})
    monkeypatch.setattr(pedido_service.historial_repository, "registrar",
                        lambda db, pid, antes, despues, uid: cambios.append((pid, antes, despues)))
    monkeypatch.setattr(pedido_service, "geocodificar", lambda d, db: (
        geocoder.ResultadoGeo(-12.12, -77.03, "Miraflores") if d in encontrados else None))
    return cambios


def test_reprocesar_saca_de_fallida_y_marca_las_no_ubicadas(monkeypatch):
    """Un pedido fallido que ahora se ubica vuelve a Listo; uno listo que no se ubica pasa a fallido (C16-03)."""
    fallido = SimpleNamespace(id=1, estado="GEOCODIFICACION_FALLIDA", direccion_destino="Av. Larco 100",
                              latitud=None, longitud=None, distrito=None)
    listo = SimpleNamespace(id=2, estado="LISTO_PARA_ENVIO", direccion_destino="Calle Inexistente 9",
                            latitud=None, longitud=None, distrito=None)
    cambios = _preparar_reproceso(monkeypatch, [fallido, listo], {"Av. Larco 100"})

    r = pedido_service.procesar_geocodificacion(db=None)

    assert (r["pedidos_exitosos"], r["pedidos_fallidos"], r["pedidos_restantes"]) == (1, 1, 0)
    assert fallido.estado == "LISTO_PARA_ENVIO" and fallido.distrito == "Miraflores"
    assert listo.estado == "GEOCODIFICACION_FALLIDA"
    assert cambios == [(1, "GEOCODIFICACION_FALLIDA", "LISTO_PARA_ENVIO"), (2, "LISTO_PARA_ENVIO", "GEOCODIFICACION_FALLIDA")]


def test_reprocesar_por_tandas_informa_lo_que_queda(monkeypatch):
    """Con tope por tanda solo se procesan los primeros y se informa cuantos quedan."""
    pedidos = [SimpleNamespace(id=i, estado="GEOCODIFICACION_FALLIDA", direccion_destino=f"Dir {i}",
                               latitud=None, longitud=None, distrito=None) for i in range(5)]
    cambios = _preparar_reproceso(monkeypatch, pedidos, set())

    r = pedido_service.procesar_geocodificacion(db=None, limite=2)

    assert (r["pedidos_fallidos"], r["pedidos_restantes"]) == (2, 3)
    assert cambios == []  # un fallido que sigue sin ubicarse no repite el historial


def test_no_se_corrige_la_ubicacion_de_un_pedido_entregado(monkeypatch):
    """Solo se puede corregir la ubicacion de pedidos no entregados ni cancelados (C17-01)."""
    entregado = SimpleNamespace(id=1, estado="ENTREGADO")
    monkeypatch.setattr(pedido_service.pedido_repository, "obtener_por_id", lambda db, pid: entregado)
    with pytest.raises(HTTPException) as e:
        pedido_service.fijar_ubicacion(None, 1, -12.1, -77.0)
    assert e.value.status_code == 400


def test_un_resultado_que_solo_ubica_el_pais_no_cuenta(monkeypatch):
    """Si Google solo reconoce "Perú" (o la region), la direccion se trata como no encontrada."""
    pais = SimpleNamespace(latitude=-9.19, longitude=-75.0, address="Perú", raw={"types": ["country", "political"]})

    class GoogleVago:
        def geocode(self, *a, **k):
            return [pais]

    monkeypatch.setattr(geocoder, "_google", GoogleVago())
    assert geocoder._buscar_google("qqzz 999", 1) == []


def test_busqueda_manual_suma_lugares_de_osm_sin_repetir(monkeypatch):
    """La busqueda del admin junta Google y OpenStreetMap y descarta el mismo lugar repetido (C17-02)."""
    g = geocoder.ResultadoGeo(-12.0464, -77.0300, "Cercado de Lima", "Plaza Mayor, Lima", "google")
    mismo = geocoder.ResultadoGeo(-12.0465, -77.0301, "Cercado de Lima", "Plaza de Armas de Lima", "nominatim")
    otro = geocoder.ResultadoGeo(-12.0700, -77.0000, "La Victoria", "Plaza de Armas, La Victoria", "nominatim")
    monkeypatch.setattr(geocoder, "_google", object())
    monkeypatch.setattr(geocoder, "_buscar_google", lambda texto, maximo: [g])
    monkeypatch.setattr(geocoder, "_buscar_osm", lambda texto, maximo: [mismo, otro])
    assert geocoder.buscar_lugares("Plaza de Armas") == [g, otro]


# --- F5: despacho y rutas (C19-01, C19-02, C20-01, C20-03) ---

from pydantic import ValidationError  # noqa: E402

from app.schemas.ruta import AsignacionBloqueRequest, OptimizacionRequest  # noqa: E402
from app.services import ruta_service  # noqa: E402


def _despacho(monkeypatch, pedidos, validar=None):
    """Simula los repositorios de asignar_bloque. Recibe los pedidos de la zona y un validador
    opcional del conductor. Devuelve la lista de pasos en el orden en que ocurrieron."""
    pasos = []
    monkeypatch.setattr(ruta_service.usuario_repository, "bloquear", lambda db, cid: pasos.append("bloquear_conductor"))

    def validar_ok(db, cid):
        pasos.append("validar_conductor")
        return SimpleNamespace(id=cid), SimpleNamespace(placa="ABC-123")
    monkeypatch.setattr(ruta_service.conductor_service, "validar_para_ruta", validar or validar_ok)
    monkeypatch.setattr(ruta_service.ruta_repository, "obtener_ruta_activa_por_conductor", lambda db, cid: None)

    def pendientes(db, distrito, bloquear=False):
        pasos.append(f"pedidos_bloqueados={bloquear}")
        return pedidos
    monkeypatch.setattr(ruta_service.pedido_repository, "obtener_pendientes_por_distrito", pendientes)
    return pasos


def test_despacho_bloquea_conductor_y_pedidos_antes_de_asignar(monkeypatch):
    """Primero se bloquea y valida al conductor y luego se toman los pedidos con candado (C19-01)."""
    pasos = _despacho(monkeypatch, [])
    with pytest.raises(HTTPException) as e:
        ruta_service.asignar_bloque(None, AsignacionBloqueRequest(distrito="Miraflores", conductor_id=7))
    assert pasos == ["bloquear_conductor", "validar_conductor", "pedidos_bloqueados=True"]
    assert e.value.status_code == 400 and "despacharla" in e.value.detail


def test_despacho_a_conductor_sin_vehiculo_se_rechaza(monkeypatch):
    """Si el conductor no pasa la validacion (sin vehiculo, de baja...) no se toca ningun pedido."""
    def sin_vehiculo(db, cid):
        raise HTTPException(status_code=400, detail="El conductor no tiene un vehículo asignado.")
    pasos = _despacho(monkeypatch, [SimpleNamespace(id=1)], validar=sin_vehiculo)
    with pytest.raises(HTTPException):
        ruta_service.asignar_bloque(None, AsignacionBloqueRequest(distrito="Miraflores", conductor_id=7))
    assert pasos == ["bloquear_conductor"]


def test_nombre_de_ruta_largo_se_rechaza():
    """El nombre personalizado de la ruta admite hasta 100 caracteres (C19-02)."""
    with pytest.raises(ValidationError):
        AsignacionBloqueRequest(nombre_ruta="R" * 101, distrito="Miraflores", conductor_id=1)


def _detalle(estado, pid, lat=-12.1, codigo=None):
    """Tupla (detalle, pedido) de una parada para las pruebas de optimizacion."""
    return (SimpleNamespace(estado_entrega=estado, secuencia=0),
            SimpleNamespace(id=pid, codigo=codigo or f"PD-{pid:03d}", latitud=lat, longitud=None if lat is None else -77.0))


def test_paradas_sin_ubicacion_solo_cuenta_pendientes():
    """Solo avisa de las paradas pendientes sin coordenadas; las ya cerradas no importan (C20-03)."""
    detalles = [_detalle("PENDIENTE", 1, lat=None), _detalle("ENTREGADO", 2, lat=None), _detalle("PENDIENTE", 3)]
    assert [p.id for p in ruta_service.paradas_sin_ubicacion(detalles)] == [1]


def test_resumen_de_optimizacion_trae_km_y_sin_ubicacion():
    """La respuesta al conductor incluye km, ahorro y los codigos sin ubicacion (C20-01, C20-03)."""
    ruta = SimpleNamespace(km_estimado=12.4, km_ahorrado=3.1)
    r = ruta_service.resumen_optimizacion("ok", [1, 2, 3], ruta, [SimpleNamespace(id=9, codigo="PD-009")])
    assert r == {"mensaje": "ok", "total_paradas": 3, "km_estimado": 12.4, "km_ahorrado": 3.1,
                 "paradas_sin_ubicacion": 1, "codigos_sin_ubicacion": ["PD-009"]}


def test_optimizar_con_todas_las_paradas_sin_ubicacion_lo_explica(monkeypatch):
    """Si ninguna parada pendiente tiene ubicacion, el error lo dice con sus codigos (C20-03)."""
    ruta = SimpleNamespace(id=1, conductor_id=5)
    monkeypatch.setattr(ruta_service.ruta_repository, "obtener_ruta_por_id", lambda db, rid: ruta)
    monkeypatch.setattr(ruta_service.ruta_repository, "obtener_detalles_con_pedido",
                        lambda db, rid: [_detalle("PENDIENTE", 4, lat=None), _detalle("ENTREGADO", 2)])
    with pytest.raises(HTTPException) as e:
        ruta_service.optimizar_ruta(None, OptimizacionRequest(ruta_id=1, latitud_actual_conductor=-12.1,
                                                               longitud_actual_conductor=-77.0), conductor_id=5)
    assert e.value.status_code == 400 and "PD-004" in e.value.detail


# ---------------- F6: entrega en campo ----------------
from app.core.imagenes import gps_de_captura  # noqa: E402
from app.schemas.parametro import ContactoConfig  # noqa: E402
from app.schemas.ruta import ActualizarEstadoRequest  # noqa: E402
from app.services import reporte_service, incidencia_service, portal_service  # noqa: E402
from app.schemas.reporte import ReporteCreate  # noqa: E402


class _BDParada:
    """Sesion falsa para actualizar_estado_parada: anota los pasos y devuelve el pedido."""

    def __init__(self, pedido):
        self.pedido, self.pasos = pedido, []

    def refresh(self, obj, with_for_update=None):
        self.pasos.append(f"bloqueo={bool(with_for_update)}")

    def rollback(self):
        self.pasos.append("rollback")

    def commit(self):
        self.pasos.append("commit")

    def query(self, *a):
        return self

    def filter(self, *a):
        return self

    def first(self):
        return self.pedido


def _parada(monkeypatch, estado_entrega, url_evidencia="/media/evidencias/x.jpg"):
    """Prepara una parada de la ruta del conductor con el estado dado. Devuelve (bd, detalle)."""
    detalle = SimpleNamespace(id=1, ruta_id=3, estado_entrega=estado_entrega, url_evidencia=url_evidencia,
                              motivo_fallo=None, fecha_gestion=None, ruta=SimpleNamespace(estado="EN_PROGRESO"))
    pedido = SimpleNamespace(id=9, codigo="PD-009", estado="EN_RUTA", fecha_entrega=None)
    monkeypatch.setattr(ruta_service, "_obtener_detalle_de_mi_ruta", lambda db, c, p: detalle)
    monkeypatch.setattr(ruta_service.incidencia_repository, "tiene_abierta", lambda db, rid: False)
    monkeypatch.setattr(ruta_service.historial_repository, "registrar", lambda *a: None)
    receptores = []
    monkeypatch.setattr(ruta_service.evidencia_repository, "fijar_receptor", lambda db, pid, n, d: receptores.append((n, d)))
    bd = _BDParada(pedido)
    bd.receptores = receptores
    return bd, detalle


def test_parada_entregada_no_puede_pasar_a_fallida(monkeypatch):
    """Una parada ya gestionada no se modifica (C26-03): 409 y nada se guarda."""
    bd, _ = _parada(monkeypatch, "ENTREGADO")
    with pytest.raises(HTTPException) as e:
        ruta_service.actualizar_estado_parada(bd, 5, 9, "FALLIDO", "Cliente ausente")
    assert e.value.status_code == 409 and "entregada" in e.value.detail
    assert "commit" not in bd.pasos


def test_reintento_del_mismo_estado_responde_sin_repetir(monkeypatch):
    """Si la cola offline reenvia la misma entrega, se responde OK sin volver a guardarla."""
    bd, _ = _parada(monkeypatch, "FALLIDO")
    r = ruta_service.actualizar_estado_parada(bd, 5, 9, "FALLIDO", "Cliente ausente")
    assert r.estado_entrega == "FALLIDO" and bd.pasos == ["bloqueo=True", "rollback"]


def test_entregar_exige_quien_recibe_y_lo_guarda(monkeypatch):
    """ENTREGADO pide nombre y documento de quien recibe (C26-02) y los guarda con la parada bloqueada."""
    bd, detalle = _parada(monkeypatch, "PENDIENTE")
    with pytest.raises(HTTPException) as e:
        ruta_service.actualizar_estado_parada(bd, 5, 9, "ENTREGADO", None)
    assert e.value.status_code == 400 and "DNI" in e.value.detail
    r = ruta_service.actualizar_estado_parada(bd, 5, 9, "ENTREGADO", None, "Ana Pérez", "45678912")
    assert r.estado_entrega == "ENTREGADO" and bd.receptores == [("Ana Pérez", "45678912")]
    assert bd.pasos[0] == "bloqueo=True" and "commit" in bd.pasos


def test_no_se_cambia_la_foto_de_una_entrega_cerrada(monkeypatch):
    """Subir otra foto POD a una parada ya entregada se rechaza antes de escribir nada."""
    _parada(monkeypatch, "ENTREGADO")
    with pytest.raises(HTTPException) as e:
        ruta_service.guardar_evidencia(None, 5, 9, b"no-importa", "x.jpg")
    assert e.value.status_code == 409


@pytest.mark.parametrize("doc, valido", [("45678912", True), ("ce0012345", True), ("1234567", False),
                                         ("45-678912", False), ("1234567890123", False)])
def test_documento_de_quien_recibe(doc, valido):
    """El documento es un DNI (8) o un carne de extranjeria: de 8 a 12 letras o numeros."""
    if valido:
        assert ActualizarEstadoRequest(estado="ENTREGADO", receptor_documento=doc).receptor_documento == doc.upper()
    else:
        with pytest.raises(ValidationError):
            ActualizarEstadoRequest(estado="ENTREGADO", receptor_documento=doc)


def test_gps_de_la_foto():
    """La ubicacion de la foto se guarda como "lat,lng"; sin dato o fuera de rango queda vacia (C26-01)."""
    assert gps_de_captura(-12.1, -77.03) == "-12.100000,-77.030000"
    assert gps_de_captura(None, -77.0) is None
    assert gps_de_captura(120.0, -77.0) is None


def test_reporte_de_pedido_ajeno_a_la_ruta_se_rechaza(monkeypatch):
    """Solo se reportan pedidos de la ruta activa del conductor (C29-02)."""
    pedido = SimpleNamespace(id=9, codigo="PD-009")
    bd = SimpleNamespace(query=lambda *a: SimpleNamespace(filter=lambda *b: SimpleNamespace(first=lambda: pedido)))
    monkeypatch.setattr(reporte_service.ruta_repository, "obtener_ruta_activa_por_conductor", lambda db, c: SimpleNamespace(id=3))
    monkeypatch.setattr(reporte_service.ruta_repository, "obtener_detalle_de_ruta", lambda db, r, p: None)
    with pytest.raises(HTTPException) as e:
        reporte_service.crear(bd, 5, ReporteCreate(pedido_id=9, motivo="Cliente ausente"))
    assert e.value.status_code == 403


def test_se_manda_ayuda_aunque_diga_que_puede_solo_y_queda_el_historial(monkeypatch):
    """C30-02: marcar 'puedo solo' ya no bloquea la ayuda. C30-01: cada envio se suma al historial."""
    inc = SimpleNamespace(id=4, estado="ABIERTA", puede_solucionar_solo=True,
                          ayuda_enviada_en=None, ayuda_enviada_por=None, ayuda_detalle=None)
    historial = []
    monkeypatch.setattr(incidencia_service.incidencia_repository, "obtener", lambda db, i: inc)
    monkeypatch.setattr(incidencia_service.incidencia_repository, "agregar_ayuda",
                        lambda db, i, d, a: historial.append(d))
    monkeypatch.setattr(incidencia_service.incidencia_repository, "guardar", lambda db: None)
    monkeypatch.setattr(incidencia_service, "_a_respuesta", lambda db, i: i)
    incidencia_service.mandar_ayuda(None, 4, 1, "Grúa", "llega en 30 min")
    incidencia_service.mandar_ayuda(None, 4, 1, "Mecánico")
    assert historial == ["Grúa: llega en 30 min", "Mecánico"] and inc.ayuda_detalle == "Mecánico"


def test_ayuda_de_antes_del_historial_se_muestra_igual(monkeypatch):
    """Una incidencia vieja (solo con la ultima ayuda en la propia fila) la devuelve como unica entrada."""
    monkeypatch.setattr(incidencia_service.incidencia_repository, "listar_ayudas", lambda db, i: [])
    vieja = SimpleNamespace(id=1, ayuda_enviada_en="2026-10-01", ayuda_detalle="Grúa")
    assert incidencia_service._ayudas(None, vieja) == [{"detalle": "Grúa", "enviada_en": "2026-10-01"}]


@pytest.mark.parametrize("tel, esperado", [("+51 987 654 321", "+51 987 654 321"), ("  ", None), (None, None)])
def test_telefono_de_coordinacion_valido(tel, esperado):
    """El telefono de coordinacion admite +, digitos y espacios; vacio lo borra (EX-13)."""
    assert ContactoConfig(telefono_coordinacion=tel).telefono_coordinacion == esperado


@pytest.mark.parametrize("tel", ["999-888-777", "12345", "llamar a Juan"])
def test_telefono_de_coordinacion_invalido(tel):
    """Un telefono con guiones, muy corto o con letras se rechaza."""
    with pytest.raises(ValidationError):
        ContactoConfig(telefono_coordinacion=tel)


def test_portal_muestra_quien_recibio_de_verdad():
    """El portal usa el nombre registrado por el conductor y enmascara el documento (C26-02)."""
    pod = SimpleNamespace(receptor_nombre="Luis Rojas", receptor_documento="45678912")
    assert portal_service._texto_recibido(pod) == "Recibido por Luis Rojas · Doc. ****912."
    assert portal_service._texto_recibido(None) == "Entregado en la dirección de destino."
