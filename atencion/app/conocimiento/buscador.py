# Recuperacion sobre la base de conocimiento (RAG simple, sin servicios de pago).
#
# Se usa BM25, el ranking clasico de los buscadores, sobre el texto normalizado:
# minusculas, sin tildes, sin palabras vacias, sinonimos propios del rubro y una "raiz"
# simple (los 6 primeros caracteres: reprogramar, reprogramo y reprogramacion -> "reprog").
# Con ~35 articulos por idioma cabe en memoria y responde en microsegundos; el indice se
# rearma cuando se edita la base de conocimiento.
import math
import re
import threading
import unicodedata
from collections import Counter
from dataclasses import dataclass

_RAIZ = 6
_K1, _B = 1.5, 0.75
_PESO_TITULO = 2   # el titulo cuenta doble

_VACIAS = {
    "es": set("""a al algo algun alguna ante con como cual cuando de del desde donde e el ella ellas ellos en entre
        era es esa ese eso esta este esto estos fue ha hay la las le les lo los me mi mis muy ni no nos o os para pero
        por que quien se si sin sobre su sus te tengo ti tu tus un una uno unos y ya yo hola buenas buenos dias tardes
        noches gracias porfa favor quiero quisiera necesito saber puedo pueden podria oe ola""".split()),
    "en": set("""a about an and are as at be but by can could do does for from have hello hi how i if in is it its
        me my of on or please so that the their them there they this to was we what when where which who why will
        with would you your thanks thank want need know""".split()),
}

# Sinonimos del rubro: se reemplazan por una palabra comun antes de indexar y de buscar.
_SINONIMOS = {
    "es": {
        "paquete": "pedido", "paquetes": "pedido", "envio": "pedido", "envios": "pedido", "encomienda": "pedido",
        "compra": "pedido", "orden": "pedido", "producto": "pedido", "pdo": "pedido",
        "demora": "tiempo", "demoran": "tiempo", "tarda": "tiempo", "tardan": "tiempo", "plazo": "tiempo",
        "rastreo": "rastrear", "seguimiento": "rastrear", "ubicar": "rastrear", "track": "rastrear",
        "reclamacion": "reclamo", "reclamaciones": "reclamo", "quejarme": "queja",
        "precio": "tarifa", "precios": "tarifa", "costo": "tarifa", "cuesta": "tarifa", "cobran": "tarifa",
        "whatsapp": "contacto", "wsp": "contacto", "telefono": "contacto", "celular": "contacto", "llamar": "contacto",
        "repartidor": "conductor", "motorizado": "conductor", "chofer": "conductor",
        "foto": "evidencia", "prueba": "evidencia",
        "recoger": "recojo", "recojan": "recojo", "recogen": "recojo",
        "cambiar": "reprogramar", "postergar": "reprogramar",
    },
    "en": {
        "package": "order", "packages": "order", "parcel": "order", "shipment": "order", "delivery": "deliver",
        "deliveries": "deliver", "tracking": "track", "where": "track",
        "price": "cost", "prices": "cost", "rates": "cost", "fee": "cost",
        "whatsapp": "contact", "phone": "contact", "call": "contact",
        "courier": "driver", "photo": "proof", "evidence": "proof",
        "complain": "claim", "complaint": "claim", "change": "reschedule",
        "collect": "pickup",
    },
}

_RE_PALABRA = re.compile(r"[a-z0-9ñ]+")


def normalizar(texto: str) -> str:
    """Minusculas y sin tildes (la ñ se conserva). Recibe el texto."""
    texto = (texto or "").lower().replace("ñ", "\x00")
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return texto.replace("\x00", "ñ")


def tokenizar(texto: str, idioma: str) -> list[str]:
    """Convierte un texto en raices buscables (sin vacias, con sinonimos). Recibe texto e idioma."""
    vacias = _VACIAS.get(idioma, set())
    sinonimos = _SINONIMOS.get(idioma, {})
    salida = []
    for palabra in _RE_PALABRA.findall(normalizar(texto)):
        # Primero el sinonimo: asi "where" (vacia en ingles) cuenta como "track".
        palabra = sinonimos.get(palabra, palabra)
        if palabra in vacias or len(palabra) < 2:
            continue
        salida.append(palabra[:_RAIZ])
    return salida


@dataclass(frozen=True)
class Resultado:
    """Un articulo recuperado con su puntaje."""
    clave: str
    idioma: str
    titulo: str
    contenido: str
    puntaje: float


class _IndiceIdioma:
    """Indice BM25 de los articulos de un idioma."""

    def __init__(self, articulos: list[dict], idioma: str):
        """Prepara frecuencias y largos. Recibe los articulos (dict) del idioma."""
        self.idioma = idioma
        self.articulos = articulos
        self.documentos: list[Counter] = []
        for a in articulos:
            fichas = tokenizar(a["titulo"], idioma) * _PESO_TITULO + tokenizar(a.get("etiquetas", ""), idioma) \
                + tokenizar(a["contenido"], idioma)
            self.documentos.append(Counter(fichas))
        self.largos = [sum(d.values()) for d in self.documentos]
        self.largo_medio = (sum(self.largos) / len(self.largos)) if self.largos else 0.0
        apariciones = Counter()
        for d in self.documentos:
            apariciones.update(d.keys())
        total = len(self.documentos)
        self.idf = {t: math.log(1 + (total - n + 0.5) / (n + 0.5)) for t, n in apariciones.items()}

    def buscar(self, consulta: str, cuantos: int) -> list[Resultado]:
        """Articulos mas parecidos a la consulta, de mayor a menor puntaje. Recibe consulta y cuantos."""
        fichas = set(tokenizar(consulta, self.idioma))
        if not fichas or not self.documentos:
            return []
        puntajes = []
        for i, doc in enumerate(self.documentos):
            puntaje = 0.0
            for t in fichas:
                frecuencia = doc.get(t, 0)
                if not frecuencia:
                    continue
                norma = _K1 * (1 - _B + _B * self.largos[i] / (self.largo_medio or 1))
                puntaje += self.idf[t] * frecuencia * (_K1 + 1) / (frecuencia + norma)
            if puntaje > 0:
                puntajes.append((puntaje, i))
        puntajes.sort(reverse=True)
        return [
            Resultado(self.articulos[i]["clave"], self.idioma, self.articulos[i]["titulo"],
                      self.articulos[i]["contenido"], round(p, 3))
            for p, i in puntajes[:cuantos]
        ]


class IndiceConocimiento:
    """Indice de toda la base de conocimiento, por idioma. Se reemplaza entero al recargar."""

    def __init__(self):
        """Empieza vacio. Sin input."""
        self._por_idioma: dict[str, _IndiceIdioma] = {}
        self._candado = threading.Lock()

    def cargar(self, articulos: list[dict]) -> None:
        """Rearma el indice con los articulos activos. Recibe dicts con clave, idioma, titulo, contenido y etiquetas."""
        nuevos = {}
        for idioma in ("es", "en"):
            nuevos[idioma] = _IndiceIdioma([a for a in articulos if a["idioma"] == idioma], idioma)
        with self._candado:
            self._por_idioma = nuevos

    def total(self) -> int:
        """Cantidad de articulos indexados (ambos idiomas). Sin input."""
        return sum(len(i.articulos) for i in self._por_idioma.values())

    def buscar(self, consulta: str, idioma: str, cuantos: int = 3, minimo: float = 0.0) -> list[Resultado]:
        """Busca en el idioma pedido; si no hay nada sobre el minimo, prueba en el otro idioma.
        Recibe consulta, idioma, cuantos y el puntaje minimo."""
        indices = self._por_idioma
        orden = [idioma] + [i for i in ("es", "en") if i != idioma]
        for actual in orden:
            indice = indices.get(actual)
            if not indice:
                continue
            resultados = [r for r in indice.buscar(consulta, cuantos) if r.puntaje >= minimo]
            if resultados:
                return resultados
        return []

    def por_clave(self, clave: str, idioma: str) -> Resultado | None:
        """Articulo por su clave e idioma (o None). Recibe clave e idioma."""
        indice = self._por_idioma.get(idioma)
        for a in (indice.articulos if indice else []):
            if a["clave"] == clave:
                return Resultado(a["clave"], idioma, a["titulo"], a["contenido"], 0.0)
        return None


indice = IndiceConocimiento()
