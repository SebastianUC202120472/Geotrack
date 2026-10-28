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
