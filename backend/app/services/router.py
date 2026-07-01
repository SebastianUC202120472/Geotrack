import math


def calcular_distancia(lat1, lon1, lat2, lon2):
    """Distancia en km entre dos puntos usando la fórmula de Haversine. Recibe lat/lon de ambos puntos."""
    R = 6371.0

    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def optimizar_secuencia_pedidos(pedidos, lat_origen, lon_origen):
    """Ordena pedidos por vecino más cercano desde el origen. Recibe lista de pedidos y lat/lon de partida."""
    pedidos_pendientes = pedidos.copy()
    ruta_optima = []

    punto_actual = (lat_origen, lon_origen)

    intentos = len(pedidos_pendientes) * 2

    while pedidos_pendientes and intentos > 0:
        intentos -= 1

        pedido_mas_cercano = None
        distancia_minima = float("inf")

        for pedido in pedidos_pendientes:
            if pedido.latitud is None or pedido.longitud is None:
                continue

            distancia = calcular_distancia(
                punto_actual[0], punto_actual[1],
                pedido.latitud, pedido.longitud,
            )

            if distancia <= distancia_minima:
                distancia_minima = distancia
                pedido_mas_cercano = pedido

        if pedido_mas_cercano:
            ruta_optima.append(pedido_mas_cercano)
            pedidos_pendientes.remove(pedido_mas_cercano)
            punto_actual = (pedido_mas_cercano.latitud, pedido_mas_cercano.longitud)
        else:
            # pedidos sin coordenadas: se agregan al final
            ruta_optima.extend(pedidos_pendientes)
            break

    return ruta_optima


def distancia_total(origen_lat, origen_lon, pedidos) -> float:
    """Suma km del recorrido de pedidos en el orden dado desde el origen. Ignora pedidos sin coordenadas."""
    total = 0.0
    actual = (origen_lat, origen_lon)
    for pedido in pedidos:
        if pedido.latitud is None or pedido.longitud is None:
            continue
        total += calcular_distancia(actual[0], actual[1], pedido.latitud, pedido.longitud)
        actual = (pedido.latitud, pedido.longitud)
    return total
