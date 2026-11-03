# Pruebas de la línea base del ahorro de rutas (C20-02): plan empírico del conductor y 2-opt.
import random
from types import SimpleNamespace

from app.services.router import (
    via_y_numero, plan_empirico, mejorar_2opt, optimizar_secuencia_pedidos, distancia_total,
    registrar_km, km_sin_optimizar,
)

ORIGEN = (-12.0560, -77.0440)


def _parada(pid, lat, lng, direccion="", distrito=None):
    """Pedido de prueba con coordenadas y dirección. Recibe id, lat, lng, dirección y distrito."""
    return SimpleNamespace(id=pid, latitud=lat, longitud=lng, direccion_destino=direccion, distrito=distrito)


def _ruta():
    """Ruta de prueba sin km calculados."""
    return SimpleNamespace(km_linea_base=None, km_estimado=None, km_ahorrado=None)


def test_via_y_numero_reconoce_la_calle():
    """La vía se reconoce aunque cambie el tipo o las tildes, y el interior no se toma como número."""
    assert via_y_numero("Av. Larco 345, Miraflores, Lima") == ("larco", 345)
    assert via_y_numero("Avenida Larco 1020 Dpto 401, Miraflores") == ("larco", 1020)
    assert via_y_numero("Jr. José Gálvez 512") == ("jose galvez", 512)
    assert via_y_numero("Av. 28 de Julio 1234, Miraflores") == ("28 de julio", 1234)
    assert via_y_numero(None) == ("", 0)


def test_plan_empirico_va_por_distrito_y_por_via():
    """El conductor termina un distrito antes de pasar al siguiente y recorre cada vía por numeración."""
    paradas = [
        _parada(1, -12.1250, -77.0290, "Av. Larco 900", "Miraflores"),
        _parada(2, -12.0980, -77.0360, "Av. Camino Real 300", "San Isidro"),
        _parada(3, -12.1200, -77.0300, "Av. Larco 300", "Miraflores"),
        _parada(4, -12.0990, -77.0350, "Av. Camino Real 500", "San Isidro"),
    ]
    orden = [p.id for p in plan_empirico(paradas, *ORIGEN)]
    assert orden == [2, 4, 3, 1]  # San Isidro está más cerca del origen; cada vía en orden de numeración


def test_plan_empirico_entra_a_la_via_por_el_extremo_mas_cercano():
    """Si el número más alto le queda más cerca, el conductor recorre la vía de bajada."""
    paradas = [
        _parada(1, -12.1300, -77.0300, "Av. Larco 100", "Miraflores"),
        _parada(2, -12.1200, -77.0300, "Av. Larco 500", "Miraflores"),
    ]
    assert [p.id for p in plan_empirico(paradas, *ORIGEN)] == [2, 1]


def test_2opt_quita_un_cruce():
    """Un recorrido que se cruza queda más corto tras el 2-opt."""
    cuadrado = [_parada(1, -12.10, -77.00), _parada(2, -12.11, -77.01), _parada(3, -12.10, -77.01), _parada(4, -12.11, -77.00)]
    origen = (-12.095, -77.00)
    antes = distancia_total(*origen, cuadrado)
    despues = distancia_total(*origen, mejorar_2opt(cuadrado, *origen))
    assert despues < antes


def test_la_ruta_optimizada_nunca_es_mas_larga_que_el_plan_ni_que_el_orden_actual():
    """En rutas al azar, la propuesta no supera al plan empírico ni al orden que ya tenía la ruta."""
    azar = random.Random(3)
    for _ in range(60):
        paradas = [
            _parada(i, -12.12 + azar.uniform(-0.02, 0.02), -77.03 + azar.uniform(-0.02, 0.02),
                    f"Calle {azar.choice('ABCDE')} {azar.randint(100, 900)}", azar.choice(["Miraflores", "Surquillo"]))
            for i in range(azar.randint(3, 15))
        ]
        propuesta = distancia_total(*ORIGEN, optimizar_secuencia_pedidos(paradas, *ORIGEN))
        assert propuesta <= distancia_total(*ORIGEN, plan_empirico(paradas, *ORIGEN)) + 1e-9
        assert propuesta <= distancia_total(*ORIGEN, paradas) + 1e-9


def test_paradas_sin_coordenadas_van_al_final():
    """Las paradas sin ubicación no entran al cálculo y quedan al final."""
    paradas = [_parada(1, None, None), _parada(2, -12.10, -77.03), _parada(3, -12.12, -77.03)]
    assert [p.id for p in optimizar_secuencia_pedidos(paradas, *ORIGEN)][-1] == 1


def test_la_linea_base_se_fija_en_la_primera_optimizacion():
    """El ahorro se mide contra el plan empírico y no se pierde si el conductor vuelve a optimizar."""
    paradas = [
        _parada(1, -12.1250, -77.0290, "Av. Larco 900", "Miraflores"),
        _parada(2, -12.1180, -77.0200, "Calle Berlín 200", "Miraflores"),
        _parada(3, -12.1200, -77.0300, "Av. Larco 300", "Miraflores"),
        _parada(4, -12.1230, -77.0210, "Calle Berlín 600", "Miraflores"),
        _parada(5, -12.1190, -77.0250, "Calle Bolognesi 150", "Miraflores"),
    ]
    ruta = _ruta()
    ordenados = optimizar_secuencia_pedidos(paradas, *ORIGEN)
    registrar_km(ruta, *ORIGEN, paradas, ordenados)
    base = ruta.km_linea_base
    assert base == round(distancia_total(*ORIGEN, plan_empirico(paradas, *ORIGEN)), 2)
    assert ruta.km_ahorrado == round(base - ruta.km_estimado, 2) >= 0
    ahorro = ruta.km_ahorrado

    # Segunda optimización a mitad de camino, desde otra posición y con el mismo orden: nada cambia.
    resto = ordenados[2:]
    posicion = (ordenados[1].latitud, ordenados[1].longitud)
    registrar_km(ruta, *posicion, resto, optimizar_secuencia_pedidos(resto, *posicion))
    assert ruta.km_linea_base == base
    assert ruta.km_ahorrado >= ahorro - 0.01


def test_ruta_cerrada_sin_optimizar_no_reclama_ahorro():
    """Si el conductor nunca optimizó, se estiman sus km y el ahorro es cero."""
    ruta = _ruta()
    km_sin_optimizar(ruta, [_parada(1, -12.10, -77.03), _parada(2, -12.12, -77.03)])
    assert ruta.km_estimado == ruta.km_linea_base > 0
    assert ruta.km_ahorrado == 0.0
