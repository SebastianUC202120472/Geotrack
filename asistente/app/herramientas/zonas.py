# Centros aproximados de los distritos de Lima Metropolitana y Callao. Sirven para
# decir "cerca de Miraflores" en vez de dar coordenadas. Es una referencia, no una
# direccion exacta: el mapa del panel sigue siendo la fuente precisa.
import math

DISTRITOS = {
    "Ancón": (-11.773, -77.176),
    "Ate": (-12.026, -76.918),
    "Barranco": (-12.149, -77.021),
    "Breña": (-12.059, -77.051),
    "Carabayllo": (-11.851, -77.034),
    "Chaclacayo": (-11.976, -76.769),
    "Chorrillos": (-12.169, -77.017),
    "Cieneguilla": (-12.075, -76.785),
    "Comas": (-11.932, -77.051),
    "El Agustino": (-12.045, -76.996),
    "Independencia": (-11.993, -77.054),
    "Jesús María": (-12.077, -77.049),
    "La Molina": (-12.083, -76.927),
    "La Victoria": (-12.072, -77.019),
    "Lima": (-12.046, -77.043),
    "Lince": (-12.085, -77.035),
    "Los Olivos": (-11.969, -77.072),
    "Lurigancho-Chosica": (-11.937, -76.697),
    "Lurín": (-12.275, -76.869),
    "Magdalena del Mar": (-12.092, -77.071),
    "Miraflores": (-12.121, -77.030),
    "Pachacámac": (-12.230, -76.861),
    "Pucusana": (-12.481, -76.797),
    "Pueblo Libre": (-12.075, -77.064),
    "Puente Piedra": (-11.866, -77.075),
    "Punta Hermosa": (-12.335, -76.826),
    "Punta Negra": (-12.366, -76.795),
    "Rímac": (-12.029, -77.032),
    "San Bartolo": (-12.389, -76.780),
    "San Borja": (-12.101, -76.999),
    "San Isidro": (-12.097, -77.036),
    "San Juan de Lurigancho": (-11.983, -77.000),
    "San Juan de Miraflores": (-12.157, -76.972),
    "San Luis": (-12.076, -76.994),
    "San Martín de Porres": (-12.007, -77.083),
    "San Miguel": (-12.077, -77.090),
    "Santa Anita": (-12.043, -76.971),
    "Santa María del Mar": (-12.405, -76.775),
    "Santa Rosa": (-11.806, -77.166),
    "Santiago de Surco": (-12.146, -76.993),
    "Surquillo": (-12.113, -77.018),
    "Villa El Salvador": (-12.213, -76.937),
    "Villa María del Triunfo": (-12.162, -76.938),
    "Callao": (-12.056, -77.118),
    "Bellavista": (-12.062, -77.106),
    "Carmen de la Legua": (-12.041, -77.093),
    "La Perla": (-12.068, -77.107),
    "La Punta": (-12.072, -77.163),
    "Ventanilla": (-11.875, -77.130),
    "Mi Perú": (-11.855, -77.123),
}

_MAX_KM = 8.0


def distancia_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Distancia Haversine en km entre dos puntos. Recibe latitudes y longitudes."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def zona_aproximada(lat, lng) -> str | None:
    """Devuelve el distrito mas cercano a un punto o None si esta lejos de Lima. Recibe lat y lng."""
    if lat is None or lng is None:
        return None
    nombre, km = min(
        ((n, distancia_km(lat, lng, c[0], c[1])) for n, c in DISTRITOS.items()),
        key=lambda par: par[1],
    )
    return nombre if km <= _MAX_KM else None
