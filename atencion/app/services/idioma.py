# Deteccion del idioma del visitante (espanol o ingles, como la landing).
# Es una heuristica sin servicios externos: cuenta palabras frecuentes de cada idioma y
# senales propias del espanol (tildes, ñ, ¿ ¡). Si no hay senales claras, se mantiene el
# idioma anterior de la conversacion o el de la pagina.
import re
import unicodedata

IDIOMAS = ("es", "en")

# Solo palabras que NO existen en el otro idioma ("a", "me", "no" o "son" se omiten a proposito).
_PALABRAS = {
    "es": set("""el la los las de del que y en un una es por para con mi mis se su lo al pedido paquete donde
        cuando como cual quiero quisiera necesito hola buenas gracias porfa favor esta estan llega llegan llego tengo
        puedo pueden oe ya aun todavia hoy ayer manana dia dias cuanto cuesta cobran reclamo queja empresa envios
        recojan entrega entregan reparten hay tienen hacen trabajan cuando sabado domingo lunes distrito distritos
        mio ustedes usted tienda llamar ayuda""".split()),
    "en": set("""the an is are of and to my i you your for with not where when how what which order package
        delivery hello hi thanks thank please can could would want need it this that today tomorrow yesterday
        cost price complaint company shipments pickup track arrive arrived hasn't haven't don't doesn't do does
        deliver saturday sunday monday help store""".split()),
}
_RE_PALABRA = re.compile(r"[a-zñ']+")


def _sin_tildes(texto: str) -> str:
    """Minusculas sin tildes, conservando la ñ. Recibe el texto."""
    texto = texto.lower().replace("ñ", "\x00")
    texto = "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")
    return texto.replace("\x00", "ñ")


def detectar(texto: str, pista: str = "es") -> str:
    """Devuelve 'es' o 'en' para un mensaje. Recibe el texto y el idioma a usar si no hay senales claras."""
    pista = pista if pista in IDIOMAS else "es"
    if not texto:
        return pista
    puntos = {"es": 0.0, "en": 0.0}
    if re.search(r"[áéíóúñ¿¡]", texto.lower()):
        puntos["es"] += 2
    for palabra in _RE_PALABRA.findall(_sin_tildes(texto)):
        for idioma in IDIOMAS:
            if palabra in _PALABRAS[idioma]:
                puntos[idioma] += 1
    if puntos["es"] == puntos["en"]:
        return pista
    return max(puntos, key=puntos.get)
