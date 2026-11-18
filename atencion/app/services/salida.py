# Salida segura de la respuesta del modelo hacia el navegador.
#
# - Texto saneado: se quitan etiquetas HTML (el widget ademas lo muestra como texto, sin HTML).
# - Enlaces solo a SAVA: un enlace a otro dominio se quita (si es [texto](url) queda el texto).
#   Se aceptan rutas relativas del sitio ("/portal").
# - Fuga de instrucciones: si la respuesta deja ver el prompt, se corta y se reemplaza.
# - Marcas internas: [CORREO_1], [TEL_1], [DNI oculto]... nunca llegan al visitante. Las del propio
#   visitante se restituyen con su valor; las que queden se cambian por "tu correo", "tu teléfono"...
#
# Como la respuesta llega por fragmentos, el filtro retiene el texto hasta el ultimo espacio:
# asi un enlace o el canario nunca quedan partidos entre dos fragmentos.
import re
from urllib.parse import urlsplit

from app.services.defensa import _normal, filtra_instrucciones

ENLACE_OMITIDO = "[enlace omitido]"
_RE_HTML = re.compile(r"<\s*/?\s*[a-zA-Z][^>]{0,500}>")
_RE_MARKDOWN = re.compile(r"!?\[([^\]\n]{0,200})\]\(([^)\s]{1,500})\)")
_RE_URL = re.compile(
    r"(?i)\b(?:(?:https?|ftp|javascript|data|file|vbscript):[^\s<>\"')\]]+"
    r"|www\.[^\s<>\"')\]]+"
    r"|(?:[a-z0-9-]{2,63}\.)+(?:com|net|org|info|io|co|pe|xyz|app|dev|me|ly|gl|link|site|online|top|ru|cn|tk|biz|us|es)"
    r"(?:/[^\s<>\"')\]]*)?)"
)
# Marcas que pone el servidor al ocultar datos (privacidad.py) y variantes que un modelo podria inventar.
_RE_MARCA_INTERNA = re.compile(
    r"(?i)\[\s*(?:(correo|email|tel|tel[eé]fono|phone)(?:[_\s-]*\d{1,2})?"
    r"|(dni|d[ií]gitos|correo|tel[eé]fono)\s+ocultos?)\s*\]")
_PALABRAS_MARCA = {
    "es": {"correo": "tu correo", "tel": "tu teléfono", "dni": "el DNI", "digitos": "los dígitos"},
    "en": {"correo": "your email", "tel": "your phone number", "dni": "the DNI", "digitos": "the digits"},
}


def quitar_marcas(texto: str, idioma: str = "es") -> str:
    """Cambia las marcas internas que queden en un texto visible por palabras normales. Recibe el texto
    y el idioma de la respuesta."""
    palabras = _PALABRAS_MARCA.get(idioma, _PALABRAS_MARCA["es"])

    def _palabra(m: re.Match) -> str:
        """Palabra que reemplaza a una marca."""
        tipo = (m.group(1) or m.group(2)).lower()
        if tipo.startswith(("correo", "email")):
            return palabras["correo"]
        if tipo.startswith(("tel", "phone")):
            return palabras["tel"]
        return palabras["dni"] if tipo == "dni" else palabras["digitos"]

    return _RE_MARCA_INTERNA.sub(_palabra, texto or "")


def _host_permitido(host: str, dominios: list[str]) -> bool:
    """True si el host es un dominio de SAVA o un subdominio suyo. Recibe host y dominios permitidos."""
    host = (host or "").lower().rstrip(".")
    return any(host == d or host.endswith("." + d) for d in dominios)


def enlace_permitido(url: str, dominios: list[str]) -> bool:
    """Decide si un enlace puede mostrarse. Recibe la URL y los dominios permitidos."""
    url = url.strip()
    if url.startswith("/") and not url.startswith("//"):
        return True   # ruta del propio sitio
    if url.startswith("#"):
        return True
    candidato = url if re.match(r"(?i)^[a-z][a-z0-9+.-]*:", url) else "https://" + url
    partes = urlsplit(candidato)
    if partes.scheme.lower() not in ("http", "https"):
        return False
    if partes.username or partes.password:
        return False   # https://sava.pe@malicioso.com
    return _host_permitido(partes.hostname or "", dominios)


def sanear(texto: str, dominios: list[str]) -> str:
    """Quita HTML y enlaces fuera de SAVA de un texto completo. Recibe texto y dominios permitidos."""
    texto = _RE_HTML.sub("", texto or "")

    def _markdown(m: re.Match) -> str:
        """Conserva el enlace si es de SAVA; si no, deja solo el texto visible."""
        return m.group(0) if enlace_permitido(m.group(2), dominios) else m.group(1)

    texto = _RE_MARKDOWN.sub(_markdown, texto)
    # Las URL sueltas se revisan fuera de los enlaces markdown que ya se aprobaron.
    partes, ultimo = [], 0
    for m in _RE_MARKDOWN.finditer(texto):
        partes.append(_filtrar_urls(texto[ultimo:m.start()], dominios))
        partes.append(m.group(0))
        ultimo = m.end()
    partes.append(_filtrar_urls(texto[ultimo:], dominios))
    return "".join(partes)


def _filtrar_urls(texto: str, dominios: list[str]) -> str:
    """Reemplaza las URL sueltas que no son de SAVA. Recibe texto y dominios."""
    return _RE_URL.sub(lambda m: m.group(0) if enlace_permitido(m.group(0), dominios) else ENLACE_OMITIDO, texto)


class FiltroSalida:
    """Filtra la respuesta en streaming: retiene hasta el ultimo espacio, sanea y vigila fugas."""

    def __init__(self, dominios: list[str], mostrar=None, prohibidas: list[str] | None = None, idioma: str = "es"):
        """Empieza sin texto retenido. Recibe los dominios permitidos, opcionalmente una funcion que prepara
        el texto visible (p. ej. devolver al visitante su propio correo en lugar de [CORREO_1]), las frases
        que un intento de jailbreak pidio repetir (si aparecen, la respuesta se descarta) y el idioma de la
        respuesta (para cambiar las marcas internas que queden por palabras normales)."""
        self._dominios = dominios
        restituir = mostrar or (lambda texto: texto)
        self._mostrar = lambda texto: quitar_marcas(restituir(texto), idioma)
        self._prohibidas = [" ".join(_normal(f).split()) for f in (prohibidas or []) if f.strip()]
        self._pendiente = ""
        self._completo = ""
        self.fuga = False

    def agregar(self, fragmento: str) -> str:
        """Recibe un fragmento del modelo y devuelve lo que ya se puede mostrar ('' si se retiene o hubo fuga)."""
        if self.fuga:
            return ""
        self._pendiente += fragmento
        self._completo += fragmento
        plano = " ".join(_normal(self._completo).split())
        if filtra_instrucciones(self._completo) or any(f in plano for f in self._prohibidas):
            self.fuga = True
            self._pendiente = ""
            return ""
        corte = max(self._pendiente.rfind(" "), self._pendiente.rfind("\n"))
        # Un enlace markdown abierto se retiene hasta que se cierre (o el texto sea demasiado largo).
        abierto = self._pendiente.rfind("[") > self._pendiente.rfind(")")
        if corte < 0 or (abierto and len(self._pendiente) < 600):
            return ""
        listo, self._pendiente = self._pendiente[:corte + 1], self._pendiente[corte + 1:]
        return self._mostrar(sanear(listo, self._dominios))

    def cerrar(self) -> str:
        """Devuelve lo que quedo retenido al terminar la respuesta. Sin input."""
        if self.fuga:
            return ""
        resto, self._pendiente = self._pendiente, ""
        return self._mostrar(sanear(resto, self._dominios))

    @property
    def texto_completo(self) -> str:
        """Todo lo que respondio el modelo, saneado y con las marcas sin restituir (para guardarlo). Sin input."""
        return sanear(self._completo, self._dominios)
