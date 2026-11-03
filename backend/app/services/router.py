import math
import re
import unicodedata


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


def _vecino_mas_cercano(pedidos, lat_origen, lon_origen) -> list:
    """Ordena por vecino más cercano desde el origen. Recibe pedidos con coordenadas y el origen."""
    pendientes = list(pedidos)
    orden = []
    actual = (lat_origen, lon_origen)
    while pendientes:
        siguiente = min(pendientes, key=lambda p: calcular_distancia(actual[0], actual[1], p.latitud, p.longitud))
        orden.append(siguiente)
        pendientes.remove(siguiente)
        actual = (siguiente.latitud, siguiente.longitud)
    return orden


def _matriz(pedidos, lat_origen, lon_origen) -> list[list[float]]:
    """Distancias entre el origen (índice 0) y cada pedido (índice i + 1). Recibe pedidos con
    coordenadas y el origen."""
    puntos = [(lat_origen, lon_origen)] + [(p.latitud, p.longitud) for p in pedidos]
    return [[calcular_distancia(a[0], a[1], b[0], b[1]) for b in puntos] for a in puntos]


def _2opt(camino: list[int], d: list[list[float]], max_pasadas: int = 50) -> list[int]:
    """Quita los cruces de un camino invirtiendo tramos mientras se acorte (2-opt). El camino sale del
    origen (índice 0, fijo) y no regresa. Recibe los índices del camino y la matriz de distancias."""
    camino = list(camino)
    n = len(camino) - 1
    for _ in range(max_pasadas):
        mejoro = False
        for i in range(1, n):
            for j in range(i + 1, n + 1):
                a, b, c = camino[i - 1], camino[i], camino[j]
                antes = d[a][b] + (d[c][camino[j + 1]] if j < n else 0.0)
                despues = d[a][c] + (d[b][camino[j + 1]] if j < n else 0.0)
                if despues < antes - 1e-9:
                    camino[i:j + 1] = reversed(camino[i:j + 1])
                    mejoro = True
        if not mejoro:
            break
    return camino


def mejorar_2opt(pedidos, lat_origen, lon_origen) -> list:
    """Quita los cruces de un recorrido (2-opt). Recibe pedidos con coordenadas en un orden y el origen."""
    orden = list(pedidos)
    camino = _2opt(list(range(len(orden) + 1)), _matriz(orden, lat_origen, lon_origen))
    return [orden[k - 1] for k in camino[1:]]


# Tipos de vía que no cuentan para reconocer la calle ("Av. Larco" y "Avenida Larco" son la misma).
_TIPOS_VIA = {"av", "avda", "avenida", "jr", "jiron", "ca", "cl", "calle", "psje", "pje", "pasaje",
              "prol", "prolongacion", "malecon", "ovalo", "alameda"}
# Lo que viene tras la numeración y no es parte de ella ("Av. Larco 345 Dpto 401").
_INTERIOR = re.compile(r"\b(dpto|dep|depto|departamento|int|interior|piso|of|oficina|torre|block|blq)\b.*")


def via_y_numero(direccion: str | None) -> tuple[str, int]:
    """Separa la vía y la numeración de una dirección ("Av. Larco 345, Miraflores" -> ("larco", 345)).
    Recibe la dirección; si no hay número devuelve 0."""
    tramo = (direccion or "").split(",")[0]
    texto = unicodedata.normalize("NFKD", tramo).encode("ascii", "ignore").decode().lower()
    texto = _INTERIOR.sub("", texto)
    palabras = re.findall(r"[a-z0-9]+", texto)
    numero = 0
    for k in range(len(palabras) - 1, -1, -1):
        if palabras[k].isdigit():
            numero = int(palabras[k])
            palabras = palabras[:k]
            break
    return " ".join(w for w in palabras if w not in _TIPOS_VIA), numero


def _distrito_de(pedido) -> str:
    """Distrito de la parada: el geocodificado o, si falta, el que sigue a la primera coma de la
    dirección. Recibe un pedido o una solicitud de recojo."""
    if getattr(pedido, "distrito", None):
        return pedido.distrito.strip().lower()
    direccion = getattr(pedido, "direccion_destino", None) or getattr(pedido, "direccion_origen", None) or ""
    partes = direccion.split(",")
    return partes[1].strip().lower() if len(partes) > 1 else ""


def plan_empirico(pedidos, lat_origen, lon_origen) -> list:
    """Orden en que un conductor arma su recorrido con la hoja impresa, sin sistema (línea base del
    ahorro, C20-02): va primero al distrito más cercano; dentro de él, a la vía más cercana, y la
    recorre por numeración desde el extremo que le queda más cerca. Recibe pedidos con coordenadas y el origen."""
    distritos: dict[str, dict[str, list]] = {}
    for p in pedidos:
        via, numero = via_y_numero(getattr(p, "direccion_destino", None) or getattr(p, "direccion_origen", None))
        distritos.setdefault(_distrito_de(p), {}).setdefault(via or f"#{p.id}", []).append((numero, p))

    def centro(grupos):
        pts = [p for g in grupos.values() for _, p in g]
        return sum(p.latitud for p in pts) / len(pts), sum(p.longitud for p in pts) / len(pts)

    def cerca(p):
        return calcular_distancia(actual[0], actual[1], p.latitud, p.longitud)

    orden = []
    actual = (lat_origen, lon_origen)
    while distritos:
        nombre = min(distritos, key=lambda k: calcular_distancia(actual[0], actual[1], *centro(distritos[k])))
        vias = distritos.pop(nombre)
        while vias:
            via = min(vias, key=lambda k: min(cerca(p) for _, p in vias[k]))
            tramo = [p for _, p in sorted(vias.pop(via), key=lambda x: x[0])]
            if cerca(tramo[-1]) < cerca(tramo[0]):
                tramo.reverse()
            orden.extend(tramo)
            actual = (tramo[-1].latitud, tramo[-1].longitud)
    return orden


def optimizar_secuencia_pedidos(pedidos, lat_origen, lon_origen):
    """Calcula el orden de visita más corto desde el origen: vecino más cercano, plan empírico del
    conductor y el orden actual, cada uno mejorado con 2-opt; se queda con el más corto. Así la ruta
    propuesta nunca es más larga que la que armaría el conductor ni que la que ya tenía. Los pedidos
    sin coordenadas van al final. Recibe la lista de pedidos (en su orden actual) y lat/lon de partida."""
    con_coordenadas = [p for p in pedidos if p.latitud is not None and p.longitud is not None]
    sin_coordenadas = [p for p in pedidos if p.latitud is None or p.longitud is None]
    if not con_coordenadas:
        return sin_coordenadas
    d = _matriz(con_coordenadas, lat_origen, lon_origen)
    indice = {id(p): k + 1 for k, p in enumerate(con_coordenadas)}
    candidatos = (
        _vecino_mas_cercano(con_coordenadas, lat_origen, lon_origen),
        plan_empirico(con_coordenadas, lat_origen, lon_origen),
        con_coordenadas,
    )
    caminos = [_2opt([0] + [indice[id(p)] for p in c], d) for c in candidatos]
    mejor = min(caminos, key=lambda cam: sum(d[cam[k]][cam[k + 1]] for k in range(len(cam) - 1)))
    return [con_coordenadas[k - 1] for k in mejor[1:]] + sin_coordenadas


def registrar_km(ruta, lat_origen, lon_origen, actuales, ordenados) -> None:
    """Guarda en la ruta el recorrido calculado y el ahorro frente al plan empírico del conductor
    (C20-02). La línea base se fija en la primera optimización; si el conductor vuelve a optimizar a
    mitad de camino, solo se ajusta el tramo que falta, sin borrar el ahorro ya medido. Recibe la ruta,
    el punto de partida, las paradas pendientes en su orden actual y en el orden nuevo."""
    km_nuevo = distancia_total(lat_origen, lon_origen, ordenados)
    if ruta.km_linea_base is None:
        ruta.km_linea_base = round(distancia_total(lat_origen, lon_origen, plan_empirico(actuales, lat_origen, lon_origen)), 2)
        ruta.km_estimado = round(km_nuevo, 2)
    else:
        km_antes = distancia_total(lat_origen, lon_origen, actuales)
        ruta.km_estimado = round(max(0.0, (ruta.km_estimado or 0.0) - km_antes + km_nuevo), 2)
    ruta.km_ahorrado = round(max(0.0, ruta.km_linea_base - ruta.km_estimado), 2)


def km_sin_optimizar(ruta, paradas) -> None:
    """Estima los km de una ruta que se cerró sin optimizar, en el orden en que se recorrió; no hay
    ahorro que atribuir al sistema. Recibe la ruta y sus paradas en orden."""
    primera = next((p for p in paradas if p.latitud is not None and p.longitud is not None), None)
    if primera is None:
        return
    ruta.km_estimado = round(distancia_total(primera.latitud, primera.longitud, paradas), 2)
    ruta.km_linea_base = ruta.km_estimado
    ruta.km_ahorrado = 0.0
