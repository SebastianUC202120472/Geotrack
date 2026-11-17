# Proteccion de datos personales del visitante (Ley 29733) antes de enviar algo al proveedor
# de IA o de guardarlo. Todo enmascarado aqui es irreversible: el modelo y la base del modulo
# nunca reciben un DNI, telefono o correo completo.
#
# - DNI: 8 digitos sueltos.
# - Ultimos digitos del DNI escritos en el chat ("mi dni termina en 1234"): tambien se ocultan,
#   porque son el dato que verifica un pedido. La verificacion real se hace con un formulario
#   propio del widget que no pasa por el modelo (semana 14).
# - Telefonos: celulares peruanos (9 digitos que empiezan en 9) y numeros con +codigo de pais.
# - Correos electronicos.
import re

_RE_DNI = re.compile(r"(?<![\w-])(\d{8})(?![\w-])")
_RE_TEL = re.compile(r"(?<![\w+])(?:\+?51[\s-]?)?9\d{2}[\s-]?\d{3}[\s-]?\d{3}(?![\w])")
_RE_TEL_INTERNACIONAL = re.compile(r"\+\d{1,3}[\s-]?\d[\d\s-]{6,14}\d")
_RE_CORREO = re.compile(r"[\w.+-]{1,64}@[\w-]{1,63}(?:\.[\w-]{1,63})+")
# "dni ... 1234", "documento termina en 1234", "last 4 digits 1234", "ID ending 1234".
_RE_DIGITOS_DNI = re.compile(
    r"(?i)(\b(?:dni|documento|doc|carn[eé]|id|digitos|dígitos|digits)\b[^\d\n]{0,30})(\d{4})(?!\d)")
# Numero de SAVA publicado en la landing: no es un dato personal y se deja visible.
_TELEFONOS_PUBLICOS = {"922507593"}


def _solo_digitos(valor: str) -> str:
    """Quita todo lo que no sea digito. Recibe el texto."""
    return re.sub(r"\D", "", valor or "")


def _tel(coincidencia: re.Match) -> str:
    """Reemplazo de un telefono, salvo el numero publico de SAVA. Recibe la coincidencia."""
    digitos = _solo_digitos(coincidencia.group(0))
    if digitos[-9:] in _TELEFONOS_PUBLICOS:
        return coincidencia.group(0)
    return "[teléfono oculto]"


class Seudonimos:
    """Cambia los correos y telefonos que escribe el visitante por marcas ([CORREO_1], [TEL_1]).
    La marca viaja al modelo y a la base; el valor real queda solo en la memoria del servidor,
    para registrar el contacto que el propio visitante confirma o para que una persona lo llame."""

    _RE_MARCA = re.compile(r"\[(CORREO|TEL)_(\d{1,2})\]")

    def __init__(self):
        """Empieza sin marcas. Sin input."""
        self._valores: dict[str, str] = {}
        self._por_valor: dict[str, str] = {}

    def _marca(self, tipo: str, valor: str) -> str:
        """Marca de un valor (la misma si se repite). Recibe el tipo y el valor."""
        if valor not in self._por_valor:
            marca = f"[{tipo}_{sum(1 for m in self._valores if m.startswith('[' + tipo)) + 1}]"
            self._valores[marca] = valor
            self._por_valor[valor] = marca
        return self._por_valor[valor]

    def ocultar(self, texto: str) -> str:
        """Reemplaza correos y telefonos por marcas. Recibe el texto."""
        if not texto:
            return texto
        texto = _RE_CORREO.sub(lambda m: self._marca("CORREO", m.group(0)), texto)

        def _telefono(m: re.Match) -> str:
            """Marca un telefono salvo el numero publico de SAVA."""
            if _solo_digitos(m.group(0))[-9:] in _TELEFONOS_PUBLICOS:
                return m.group(0)
            return self._marca("TEL", " ".join(m.group(0).split()))

        texto = _RE_TEL_INTERNACIONAL.sub(_telefono, texto)
        return _RE_TEL.sub(_telefono, texto)

    def valor(self, marca: str) -> str | None:
        """Valor real de una marca, o None si no existe. Recibe la marca."""
        return self._valores.get((marca or "").strip())

    def restituir(self, texto: str) -> str:
        """Devuelve los valores reales en un texto que se muestra al MISMO visitante. Recibe el texto."""
        return self._RE_MARCA.sub(lambda m: self._valores.get(m.group(0), m.group(0)), texto or "")


def enmascarar_texto(texto: str) -> str:
    """Oculta DNI, ultimos digitos de DNI, telefonos y correos dentro de un texto libre. Recibe el texto."""
    if not texto:
        return texto
    texto = _RE_CORREO.sub("[correo oculto]", texto)
    texto = _RE_TEL_INTERNACIONAL.sub(_tel, texto)
    texto = _RE_TEL.sub(_tel, texto)
    texto = _RE_DNI.sub("[DNI oculto]", texto)
    return _RE_DIGITOS_DNI.sub(lambda m: m.group(1) + "[dígitos ocultos]", texto)
