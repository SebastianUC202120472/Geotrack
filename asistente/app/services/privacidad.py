# Proteccion de datos personales antes de enviar algo al proveedor de IA.
#
# - Lo que escribe el usuario: cada DNI o telefono se cambia por una marca ([DNI_1],
#   [TEL_1]). La marca viaja al modelo; el valor real se queda en el servidor y se
#   restituye solo al ejecutar la consulta y al mostrar la respuesta al mismo usuario.
# - Lo que devuelve el nucleo: DNI y telefonos se enmascaran de forma irreversible
#   (4567••12). El modelo nunca recibe un DNI o telefono completo de un tercero.
import re

# DNI peruano: 8 digitos sueltos (no parte de un numero mas largo ni de un codigo).
_RE_DNI = re.compile(r"(?<![\w-])(\d{8})(?![\w-])")
# Celular peruano: 9 digitos empezando en 9, con o sin +51 y espacios.
_RE_TEL = re.compile(r"(?<![\w])(?:\+?51[\s-]?)?(9\d{2}[\s-]?\d{3}[\s-]?\d{3})(?![\w])")
_RE_MARCA = re.compile(r"\[(DNI|TEL)_(\d{1,3})\]")

# Campos del nucleo que nunca se envian completos al modelo.
_CAMPOS_DNI = {"dni", "dni_destinatario"}
_CAMPOS_TEL = {"telefono", "telefono_destinatario", "celular"}
_CAMPOS_FUERA = {"licencia_numero", "foto_url", "url_evidencia", "clave", "contrasena", "token"}


def enmascarar_dni(valor: str) -> str:
    """Deja visibles los 2 primeros y 2 ultimos digitos de un DNI. Recibe el DNI."""
    digitos = re.sub(r"\D", "", valor or "")
    if len(digitos) < 5:
        return "••••"
    return digitos[:2] + "•" * (len(digitos) - 4) + digitos[-2:]


def enmascarar_telefono(valor: str) -> str:
    """Deja visibles solo los 2 ultimos digitos de un telefono. Recibe el telefono."""
    digitos = re.sub(r"\D", "", valor or "")
    if len(digitos) < 3:
        return "•••"
    return "9•• ••• •" + digitos[-2:]


def enmascarar_correo(valor: str) -> str:
    """Enmascara un correo: 'ab***@dominio'. Recibe el correo."""
    if not valor or "@" not in valor:
        return valor or ""
    usuario, dominio = valor.split("@", 1)
    return usuario[:2] + "***@" + dominio


def enmascarar_texto(texto: str) -> str:
    """Enmascara DNI y telefonos que aparezcan dentro de un texto libre. Recibe el texto."""
    if not texto:
        return texto
    texto = _RE_TEL.sub(lambda m: enmascarar_telefono(m.group(1)), texto)
    return _RE_DNI.sub(lambda m: enmascarar_dni(m.group(1)), texto)


def sanear_datos(datos, max_texto: int = 400):
    """Recorre un resultado del nucleo y enmascara DNI, telefonos y textos largos. Recibe dict/lista/valor."""
    if isinstance(datos, dict):
        limpio = {}
        for clave, valor in datos.items():
            clave_min = str(clave).lower()
            if clave_min in _CAMPOS_FUERA:
                continue
            if clave_min in _CAMPOS_DNI and valor:
                limpio[clave] = enmascarar_dni(str(valor))
            elif clave_min in _CAMPOS_TEL and valor:
                limpio[clave] = enmascarar_telefono(str(valor))
            else:
                limpio[clave] = sanear_datos(valor, max_texto)
        return limpio
    if isinstance(datos, list):
        return [sanear_datos(v, max_texto) for v in datos]
    if isinstance(datos, str):
        texto = enmascarar_texto(datos)
        return texto if len(texto) <= max_texto else texto[:max_texto] + "…"
    return datos


class Seudonimos:
    """Cambia DNI y telefonos escritos por el usuario por marcas y los restituye despues."""

    def __init__(self):
        self._valores: dict[str, str] = {}   # marca -> valor real
        self._marcas: dict[str, str] = {}    # valor normalizado -> marca
        self._contador = {"DNI": 0, "TEL": 0}

    def _marca_para(self, tipo: str, valor: str) -> str:
        """Devuelve la marca de un valor (la misma si se repite). Recibe tipo y valor."""
        normal = re.sub(r"\D", "", valor)
        if tipo == "TEL" and len(normal) == 11 and normal.startswith("51"):
            normal = normal[2:]
        llave = f"{tipo}:{normal}"
        if llave not in self._marcas:
            self._contador[tipo] += 1
            marca = f"[{tipo}_{self._contador[tipo]}]"
            self._marcas[llave] = marca
            self._valores[marca] = normal
        return self._marcas[llave]

    def ocultar(self, texto: str) -> str:
        """Reemplaza DNI y telefonos de un texto por marcas. Recibe el texto del usuario."""
        if not texto:
            return texto
        texto = _RE_TEL.sub(lambda m: self._marca_para("TEL", m.group(1)), texto)
        return _RE_DNI.sub(lambda m: self._marca_para("DNI", m.group(1)), texto)

    def restituir(self, texto: str) -> str:
        """Devuelve los valores reales en lugar de las marcas conocidas. Recibe el texto."""
        if not texto:
            return texto
        return _RE_MARCA.sub(lambda m: self._valores.get(m.group(0), m.group(0)), texto)

    def restituir_argumentos(self, datos):
        """Restituye las marcas dentro de los argumentos de una funcion. Recibe dict/lista/valor."""
        if isinstance(datos, dict):
            return {k: self.restituir_argumentos(v) for k, v in datos.items()}
        if isinstance(datos, list):
            return [self.restituir_argumentos(v) for v in datos]
        if isinstance(datos, str):
            return self.restituir(datos)
        return datos

    def tiene_marcas(self) -> bool:
        """Dice si se oculto algun dato en este mensaje. Sin input."""
        return bool(self._valores)


ENLACE_OMITIDO = "[enlace externo omitido]"
# Enlace en Markdown "[texto](url)": queda solo el texto. URL suelta: se reemplaza por un aviso.
_RE_ENLACE_MD = re.compile(r"\]\((?:https?://|www\.)[^)\s]*\)", re.I)
_RE_URL = re.compile(r"\b(?:https?://|www\.)[^\s<>\"'`)\]]+", re.I)


class FiltroSalida:
    """Limpia la respuesta del modelo antes de mostrarla, aunque llegue partida en el streaming
    (retiene la ultima palabra hasta saber como termina):
    - nombres internos de las funciones -> su nombre visible (no revelar la configuracion);
    - URLs absolutas -> se quitan: los enlaces al panel los arma el servidor, nunca el modelo.
    Recibe el mapa {nombre_interno: nombre_visible}."""

    def __init__(self, nombres: dict[str, str]):
        self._nombres = nombres
        alternativas = "|".join(sorted(map(re.escape, nombres), key=len, reverse=True))
        self._patron = re.compile(rf"`?(?<![\w])({alternativas})(?![\w])`?") if nombres else None
        self._pendiente = ""

    def _reemplazar(self, texto: str) -> str:
        """Aplica los reemplazos a un texto completo. Recibe el texto."""
        if not texto:
            return texto
        # La puntuacion final ("…/x.") es de la oracion, no del enlace: se conserva.
        texto = _RE_URL.sub(lambda m: ENLACE_OMITIDO + m.group(0)[len(m.group(0).rstrip(".,;:!?")):],
                            _RE_ENLACE_MD.sub("]", texto))
        if not self._patron:
            return texto
        return self._patron.sub(lambda m: self._nombres[m.group(1)], texto)

    def agregar(self, fragmento: str) -> str:
        """Agrega un fragmento y devuelve lo que ya se puede mostrar. Recibe el fragmento."""
        self._pendiente += fragmento
        cola = re.search(r"\S*$", self._pendiente)
        corte = cola.start() if cola else len(self._pendiente)
        listo, self._pendiente = self._pendiente[:corte], self._pendiente[corte:]
        return self._reemplazar(listo)

    def cerrar(self) -> str:
        """Devuelve lo retenido al terminar el flujo. Sin input."""
        resto, self._pendiente = self._pendiente, ""
        return self._reemplazar(resto)


# Fila de una tabla Markdown: "| a | b |" o la linea separadora "---|:---:|---".
_RE_FILA_TABLA = re.compile(r"^\|.*\|$")
_RE_SEPARADOR_TABLA = re.compile(r"^\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?$")
# Inicio de linea que todavia podria ser parte de una tabla (solo |, -, : y espacios).
_RE_QUIZA_TABLA = re.compile(r"^[|:\-\s]*$")


def es_fila_tabla(linea: str) -> bool:
    """Dice si una linea completa es una fila o separador de tabla Markdown. Recibe la linea."""
    s = linea.strip()
    return bool(s) and (bool(_RE_FILA_TABLA.match(s)) and s.count("|") >= 2 or bool(_RE_SEPARADOR_TABLA.match(s)))


class FiltroTablas:
    """Quita las tablas Markdown que el modelo escriba en el texto, aunque lleguen partidas en el
    streaming: el detalle va en la tabla que arma el servidor con los datos reales.
    Solo retiene la linea en curso si empieza como una tabla; el resto pasa al instante."""

    def __init__(self):
        self._linea = ""      # inicio de la linea en curso, retenido hasta saber si es tabla
        self._libre = False   # la linea en curso ya se sabe que no es tabla: pasa directo
        self._previa_tabla = False
        self.quito_tabla = False

    def _soltar_linea(self, linea: str) -> str:
        """Decide sobre una linea completa (con su salto). Recibe la linea sin el salto."""
        if es_fila_tabla(linea):
            self.quito_tabla = True
            self._previa_tabla = True
            return ""
        # La linea vacia que sigue a una tabla quitada tambien se omite (no deja huecos dobles).
        if self._previa_tabla and not linea.strip():
            return ""
        self._previa_tabla = False
        return linea + "\n"

    def agregar(self, fragmento: str) -> str:
        """Agrega un fragmento y devuelve lo que ya se puede mostrar. Recibe el fragmento."""
        salida = []
        partes = fragmento.split("\n")
        for i, parte in enumerate(partes):
            fin_de_linea = i < len(partes) - 1
            if self._libre:
                salida.append(parte + ("\n" if fin_de_linea else ""))
                if fin_de_linea:
                    self._libre = False
                continue
            self._linea += parte
            if fin_de_linea:
                salida.append(self._soltar_linea(self._linea))
                self._linea = ""
            elif self._linea.strip() and not self._linea.lstrip().startswith("|") and not _RE_QUIZA_TABLA.match(self._linea):
                self._previa_tabla = False
                salida.append(self._linea)
                self._linea = ""
                self._libre = True
        return "".join(salida)

    def cerrar(self) -> str:
        """Devuelve lo retenido al terminar el flujo. Sin input."""
        resto, self._linea, self._libre = self._linea, "", False
        if not resto or es_fila_tabla(resto):
            self.quito_tabla = self.quito_tabla or bool(resto)
            return ""
        return resto


def quitar_tablas(texto: str) -> str:
    """Quita las tablas Markdown de un texto completo. Recibe el texto."""
    filtro = FiltroTablas()
    return (filtro.agregar(texto) + filtro.cerrar()).rstrip("\n") if texto else texto


class RestituidorFlujo:
    """Restituye marcas en un texto que llega por partes (streaming) sin cortar una marca a la mitad."""

    def __init__(self, seudonimos: Seudonimos):
        self._seudonimos = seudonimos
        self._pendiente = ""

    def agregar(self, fragmento: str) -> str:
        """Agrega un fragmento y devuelve lo que ya se puede mostrar. Recibe el fragmento."""
        self._pendiente += fragmento
        corte = self._pendiente.rfind("[")
        if corte != -1 and "]" not in self._pendiente[corte:] and len(self._pendiente) - corte <= 10:
            listo, self._pendiente = self._pendiente[:corte], self._pendiente[corte:]
        else:
            listo, self._pendiente = self._pendiente, ""
        return self._seudonimos.restituir(listo)

    def cerrar(self) -> str:
        """Devuelve lo que quedaba retenido al terminar el flujo. Sin input."""
        resto, self._pendiente = self._pendiente, ""
        return self._seudonimos.restituir(resto)
