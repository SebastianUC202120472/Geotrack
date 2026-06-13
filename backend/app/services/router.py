# app/services/router.py
# ============================================================================
# CAPA: SERVICIO (motor matemático) — Optimización de rutas / VRP (CUS-19)
# ----------------------------------------------------------------------------
# ¿QUÉ HACE?  Decide EN QUÉ ORDEN visitar los pedidos para recorrer la menor
#             distancia posible. Es el "cerebro" del enrutamiento.
# ¿CÓMO?      Algoritmo del "Vecino Más Cercano" (greedy): desde el punto
#             actual, siempre va al pedido más cercano que falte por visitar.
#             La distancia se calcula con la fórmula de Haversine (distancia
#             real sobre la superficie de la Tierra).
# ¿CON QUÉ SE CONECTA?
#   - Lo USA: services/ruta_service.py (función optimizar_ruta, CUS-19).
# ============================================================================
import math


def calcular_distancia(lat1, lon1, lat2, lon2):
    """
    Fórmula de Haversine: distancia en KM entre dos puntos (lat/lon) sobre la Tierra.
    """
    R = 6371.0  # Radio de la Tierra en km

    # Convertir grados a radianes (lo que necesitan las funciones trigonométricas).
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    # Fórmula de Haversine.
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def optimizar_secuencia_pedidos(pedidos, lat_origen, lon_origen):
    """
    Ordena la lista de 'pedidos' empezando desde (lat_origen, lon_origen).
    Devuelve la misma lista pero en el orden óptimo de visita.

    Garantía: procesa TODOS los pedidos; si alguno no tiene coordenadas, lo
    añade al final sin perderlo.
    """
    pedidos_pendientes = pedidos.copy()
    ruta_optima = []

    punto_actual = (lat_origen, lon_origen)

    # Tope de seguridad para evitar bucles infinitos.
    intentos = len(pedidos_pendientes) * 2

    while pedidos_pendientes and intentos > 0:
        intentos -= 1

        pedido_mas_cercano = None
        distancia_minima = float("inf")

        # Buscamos, entre los que faltan, el más cercano al punto actual.
        for pedido in pedidos_pendientes:
            if pedido.latitud is None or pedido.longitud is None:
                continue  # sin coordenadas: no se puede medir, lo saltamos por ahora

            distancia = calcular_distancia(
                punto_actual[0], punto_actual[1],
                pedido.latitud, pedido.longitud,
            )

            # '<=' maneja el caso de dos pedidos en la misma coordenada (distancia 0).
            if distancia <= distancia_minima:
                distancia_minima = distancia
                pedido_mas_cercano = pedido

        if pedido_mas_cercano:
            # Lo añadimos a la ruta y nos "movemos" hasta él.
            ruta_optima.append(pedido_mas_cercano)
            pedidos_pendientes.remove(pedido_mas_cercano)
            punto_actual = (pedido_mas_cercano.latitud, pedido_mas_cercano.longitud)
        else:
            # No quedó ninguno medible (sin coordenadas): los agregamos al final.
            ruta_optima.extend(pedidos_pendientes)
            break

    return ruta_optima
