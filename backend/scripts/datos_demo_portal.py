# Catalogo de datos de la demostracion del portal de clientes.
# Modulo PURO: sin base de datos ni efectos secundarios, para poder testearlo aparte.
# Lo consume scripts/seed_portal_demo.py.

# Las cinco empresas cliente. La clave es de DEMOSTRACION: se guarda hasheada con
# Argon2 en la BD, pero se deja fija y legible para poder teclearla en la sustentacion.
EMPRESAS = [
    {
        "razon_social": "Ripley S.A.",
        "ruc": "20337564373",
        "direccion_origen": "Av. Separadora Industrial 2085, Ate, Lima, Peru",
        "codigo_acceso": "RIPLEY",
        "clave": "Ripley2026",
        "correo_portal": "logistica@ripley.com.pe",
        "prefijo_ref": "RPL",
    },
    {
        "razon_social": "Saga Falabella S.A.",
        "ruc": "20100128056",
        "direccion_origen": "Av. Los Frutales 220, Ate, Lima, Peru",
        "codigo_acceso": "FALABELLA",
        "clave": "Falabella2026",
        "correo_portal": "despachos@sagafalabella.com.pe",
        "prefijo_ref": "SGF",
    },
    {
        "razon_social": "Tiendas Oechsle S.A.",
        "ruc": "20553559194",
        "direccion_origen": "Av. Nicolas Ayllon 2775, Ate, Lima, Peru",
        "codigo_acceso": "OECHSLE",
        "clave": "Oechsle2026",
        "correo_portal": "logistica@oechsle.pe",
        "prefijo_ref": "OEC",
    },
    {
        "razon_social": "Promart Homecenter",
        "ruc": "20536557858",
        "direccion_origen": "Av. Santa Rosa 550, Lurin, Lima, Peru",
        "codigo_acceso": "PROMART",
        "clave": "Promart2026",
        "correo_portal": "reparto@promart.pe",
        "prefijo_ref": "PRM",
    },
    {
        "razon_social": "Plaza Vea",
        "ruc": "20100070970",
        "direccion_origen": "Av. Los Fresnos 175, Villa El Salvador, Lima, Peru",
        "codigo_acceso": "PLAZAVEA",
        "clave": "PlazaVea2026",
        "correo_portal": "ecommerce@plazavea.com.pe",
        "prefijo_ref": "PZV",
    },
]

# Distritos de reparto con coordenadas aproximadas de su centro. Se siembran fijas para
# no gastar cuota del geocodificador con 250 direcciones.
DISTRITOS = {
    "Miraflores": (-12.1211, -77.0300),
    "San Isidro": (-12.0972, -77.0365),
    "Santiago de Surco": (-12.1450, -76.9920),
    "San Miguel": (-12.0770, -77.0830),
    "La Molina": (-12.0790, -76.9450),
    "Jesus Maria": (-12.0740, -77.0490),
    "Pueblo Libre": (-12.0740, -77.0630),
    "Barranco": (-12.1490, -77.0210),
    "Surquillo": (-12.1120, -77.0110),
    "San Borja": (-12.1080, -77.0000),
    "Lince": (-12.0870, -77.0360),
    "Magdalena del Mar": (-12.0900, -77.0740),
}

# Zonas donde se concentran los pedidos sin asignar. El panel agrupa los pendientes por
# distrito, asi que juntarlos en pocas zonas hace que la ruta armada en vivo durante la
# sustentacion tenga una decena de paradas en vez de dos.
DISTRITOS_PENDIENTES = ("Miraflores", "San Isidro", "Santiago de Surco")

# Cuotas de estados por empresa (50 pedidos cada una).
CUOTAS = (
    ("ENTREGADO", 30),
    ("EN_RUTA", 6),
    ("LISTO_PARA_ENVIO", 8),
    ("FALLIDO", 3),
    ("OBSERVADO", 3),
)

_NOMBRES = (
    "Jose", "Maria", "Luis", "Ana", "Carlos", "Rosa", "Miguel", "Carmen", "Jorge", "Elena",
    "Pedro", "Lucia", "Victor", "Sofia", "Raul", "Patricia", "Diego", "Claudia", "Andres", "Milagros",
)
_APELLIDOS = (
    "Quispe", "Vargas", "Mendoza", "Rojas", "Flores", "Huaman", "Castillo", "Ramos", "Chavez", "Ponce",
    "Salazar", "Cordova", "Guerrero", "Paredes", "Bautista", "Zegarra", "Ninaquispe", "Tapia", "Arce", "Bravo",
)
_VIAS = (
    "Av. Larco", "Av. Pardo", "Av. Benavides", "Jr. Berlin", "Av. Angamos", "Calle Los Pinos",
    "Av. Primavera", "Jr. Independencia", "Av. La Marina", "Calle Los Nogales", "Av. Arequipa",
    "Jr. Huascar", "Av. Javier Prado", "Calle Las Begonias", "Av. Republica de Panama",
)


def reparto_estados(total: int = 50) -> list:
    """Devuelve la lista de estados de los pedidos de una empresa. Recibe el total (50).
    Respeta las cuotas de CUOTAS y ajusta el ultimo tramo si el total no es 50."""
    estados = []
    for estado, cantidad in CUOTAS:
        estados.extend([estado] * round(cantidad * total / 50))
    while len(estados) > total:
        estados.pop()
    while len(estados) < total:
        estados.append("ENTREGADO")
    return estados


def destinatario(indice: int) -> dict:
    """Construye un destinatario deterministico. Recibe el indice global del pedido (0..249).
    El DNI es unico por indice para que el rastreo por persona sea inequivoco."""
    nombre = _NOMBRES[indice % len(_NOMBRES)]
    apellido = _APELLIDOS[(indice // len(_NOMBRES)) % len(_APELLIDOS)]
    return {
        "nombre": f"{nombre} {apellido}",
        "telefono": f"9{10000000 + indice * 37:08d}"[:9],
        "dni": f"{41000000 + indice * 7:08d}",
    }


def direccion(indice: int, distrito: str) -> str:
    """Arma una direccion de entrega. Recibe el indice del pedido y el distrito.
    El formato deja el distrito justo tras la primera coma porque el backend lo extrae
    de ahi (partes[1]) al procesar la direccion."""
    via = _VIAS[indice % len(_VIAS)]
    numero = 100 + (indice * 13) % 1800
    return f"{via} {numero}, {distrito}, Lima, Peru"
