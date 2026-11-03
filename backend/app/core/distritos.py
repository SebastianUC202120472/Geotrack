# Distritos de Lima Metropolitana y del Callao (C16-01). Sirve para que la zona de un pedido
# salga del resultado del geocodificador (o, en su defecto, de cualquier parte del texto de la
# direccion) y siempre con el mismo nombre, en vez de copiar el texto tras la primera coma.
import re
import unicodedata

ZONA_DESCONOCIDA = "ZONA_DESCONOCIDA"

# Nombre oficial de cada distrito (43 de Lima + 7 del Callao).
DISTRITOS_LIMA = (
    "Ancón", "Ate", "Barranco", "Breña", "Carabayllo", "Cercado de Lima", "Chaclacayo", "Chorrillos",
    "Cieneguilla", "Comas", "El Agustino", "Independencia", "Jesús María", "La Molina", "La Victoria",
    "Lince", "Los Olivos", "Lurigancho", "Lurín", "Magdalena del Mar", "Miraflores", "Pachacámac",
    "Pucusana", "Pueblo Libre", "Puente Piedra", "Punta Hermosa", "Punta Negra", "Rímac", "San Bartolo",
    "San Borja", "San Isidro", "San Juan de Lurigancho", "San Juan de Miraflores", "San Luis",
    "San Martín de Porres", "San Miguel", "Santa Anita", "Santa María del Mar", "Santa Rosa",
    "Santiago de Surco", "Surquillo", "Villa El Salvador", "Villa María del Triunfo",
    "Bellavista", "Callao", "Carmen de la Legua Reynoso", "La Perla", "La Punta", "Mi Perú", "Ventanilla",
)

# "Lima" y "Callao" tambien son el nombre de la provincia: solo cuentan si no aparece otro distrito.
GENERICOS = {"Cercado de Lima", "Callao"}

# Formas abreviadas o antiguas con las que se escriben algunos distritos.
_ALIAS = {
    "LIMA": "Cercado de Lima",
    "CERCADO": "Cercado de Lima",
    "LIMA CERCADO": "Cercado de Lima",
    "CERCADO LIMA": "Cercado de Lima",
    "SURCO": "Santiago de Surco",
    "MAGDALENA": "Magdalena del Mar",
    "SJL": "San Juan de Lurigancho",
    "SJM": "San Juan de Miraflores",
    "SMP": "San Martín de Porres",
    "SAN MARTIN DE PORRAS": "San Martín de Porres",
    "VES": "Villa El Salvador",
    "VMT": "Villa María del Triunfo",
    "CHOSICA": "Lurigancho",
    "LURIGANCHO CHOSICA": "Lurigancho",
    "ATE VITARTE": "Ate",
    "VITARTE": "Ate",
    "CARMEN DE LA LEGUA": "Carmen de la Legua Reynoso",
    "CALLAO CERCADO": "Callao",
    "CERCADO DEL CALLAO": "Callao",
}

# Prefijos que acompañan al nombre en los resultados de los mapas ("Distrito de Ate").
_PREFIJOS = re.compile(
    r"^(MUNICIPALIDAD (DISTRITAL|PROVINCIAL|METROPOLITANA) DE |MUNICIPALIDAD DE |DISTRITO DE |DISTRITO |"
    r"PROVINCIA CONSTITUCIONAL DEL |PROVINCIA DE |PROVINCIA |PROV\. )"
)


def _clave(texto: str) -> str:
    """Pasa un texto a mayusculas sin tildes, sin numeros ni signos (p. ej. codigo postal). Recibe el texto."""
    sin_tildes = "".join(
        c for c in unicodedata.normalize("NFKD", texto or "") if not unicodedata.combining(c)
    )
    limpio = re.sub(r"[^A-Z ]", " ", sin_tildes.upper())
    limpio = re.sub(r"\s+", " ", limpio).strip()
    return _PREFIJOS.sub("", limpio).strip()


_POR_CLAVE = {_clave(d): d for d in DISTRITOS_LIMA}
_POR_CLAVE.update(_ALIAS)


def normalizar_distrito(texto: str | None) -> str | None:
    """Devuelve el nombre oficial del distrito si el texto es uno de Lima/Callao, o None. Recibe el texto."""
    if not texto:
        return None
    return _POR_CLAVE.get(_clave(texto))


def elegir_distrito(candidatos) -> str | None:
    """Escoge el primer distrito reconocido de una lista de textos, prefiriendo uno especifico sobre
    "Lima"/"Callao" (que tambien son provincia). Recibe un iterable de textos (puede tener None)."""
    generico = None
    for texto in candidatos:
        distrito = normalizar_distrito(texto)
        if distrito is None:
            continue
        if distrito not in GENERICOS:
            return distrito
        generico = generico or distrito
    return generico


def distrito_desde_texto(direccion: str | None) -> str | None:
    """Busca el distrito en cualquier tramo de la direccion separado por comas o guiones
    ("Av. Larco 123, Miraflores, Lima"). Recibe la direccion; devuelve el nombre oficial o None."""
    tramos = re.split(r",| - ", direccion or "")
    # El primer tramo es la calle: se mira al final para no confundir "Av. Miraflores" con el distrito.
    return elegir_distrito(tramos[1:] + tramos[:1])


def resolver_distrito(distrito_geo: str | None, direccion: str | None) -> str:
    """Distrito final de un punto geocodificado: el que dio el mapa, si no el del texto, si no
    ZONA_DESCONOCIDA. Recibe el distrito del geocodificador (o None) y la direccion escrita."""
    return elegir_distrito([distrito_geo, distrito_desde_texto(direccion)]) or ZONA_DESCONOCIDA
