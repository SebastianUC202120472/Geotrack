# Lista CERRADA de funciones que el modelo puede pedir (OWASP LLM06/LLM07). No hay SQL ni
# direcciones libres: cada funcion tiene su esquema y sus argumentos se validan aqui antes de
# ejecutarse. Solo existen estas cinco:
#   buscar_conocimiento  consulta la base de conocimiento.
#   rastrear_pedido      resumen enmascarado; el detalle solo si el visitante verifico con su DNI
#                        en el formulario del widget (los digitos nunca pasan por el modelo).
#   reprogramar_entrega  solo PROPONE: el visitante confirma con un clic en la tarjeta.
#   registrar_contacto   solo PROPONE: el visitante confirma con un clic en la tarjeta.
#   derivar_a_persona    deja la conversacion en la bandeja del equipo.
import re

from app.herramientas.cliente_portal import codigo_valido


class ArgumentoInvalido(ValueError):
    """Argumentos que no cumplen el esquema de la funcion."""


def _funcion(nombre: str, descripcion: str, propiedades: dict, requeridos: list[str]) -> dict:
    """Arma la definicion de una funcion en el formato de la API. Recibe nombre, descripcion, propiedades y requeridos."""
    return {"type": "function", "function": {
        "name": nombre, "description": descripcion,
        "parameters": {"type": "object", "properties": propiedades, "required": requeridos},
    }}


_TEXTO = {"type": "string"}
HERRAMIENTAS = [
    _funcion("buscar_conocimiento",
             "Busca en la base de conocimiento de SAVA (cobertura, días, servicio, reprogramación, reclamos, contacto, "
             "empresas). Úsala cuando la información recibida no alcance para responder.",
             {"consulta": {**_TEXTO, "description": "Qué buscar, con palabras clave (máx. 200 caracteres)."}},
             ["consulta"]),
    _funcion("rastrear_pedido",
             "Consulta el estado de un pedido por su código (p. ej. PD-001). Si el visitante aún no verificó el pedido, "
             "el sistema le muestra un formulario para los últimos 4 dígitos del DNI del destinatario.",
             {"codigo": {**_TEXTO, "description": "Código del pedido tal como lo escribió el visitante."}},
             ["codigo"]),
    _funcion("reprogramar_entrega",
             "Propone reprogramar la entrega de un pedido YA verificado en una de las franjas disponibles. No cambia "
             "nada: muestra una tarjeta y el visitante decide con Confirmar o Cancelar.",
             {"codigo": _TEXTO, "franja": {**_TEXTO, "description": "Una de las franjas exactas que devolvió rastrear_pedido."}},
             ["codigo", "franja"]),
    _funcion("registrar_contacto",
             "Propone registrar a una empresa interesada en el servicio para que el equipo comercial le envíe una "
             "propuesta. No registra nada: muestra una tarjeta y el visitante decide. Pide antes los datos que falten.",
             {"nombre": _TEXTO, "empresa": _TEXTO,
              "correo": {**_TEXTO, "description": "La marca [CORREO_n] que aparece en la conversación."},
              "telefono": {**_TEXTO, "description": "La marca [TEL_n] que aparece en la conversación (opcional)."},
              "volumen_diario": {"type": "integer", "description": "Pedidos por día aproximados (opcional)."},
              "necesidad": {**_TEXTO, "description": "Qué necesita distribuir y en qué zonas (opcional, breve)."}},
             ["nombre", "correo"]),
    _funcion("derivar_a_persona",
             "Deja la conversación para que una persona del equipo de SAVA la atienda. Úsala si el visitante lo pide "
             "o si no puedes resolver su caso.",
             {"motivo": {**_TEXTO, "description": "Resumen breve del caso (máx. 200 caracteres), sin datos personales."},
              "contacto": {**_TEXTO, "description": "Marca [CORREO_n] o [TEL_n] si el visitante quiere que lo contacten (opcional)."}},
             ["motivo"]),
]
NOMBRES = {h["function"]["name"] for h in HERRAMIENTAS}
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")
_RE_MARCA_CORREO = re.compile(r"^\[CORREO_\d{1,2}\]$")
_RE_MARCA_TEL = re.compile(r"^\[TEL_\d{1,2}\]$")
_RE_MARCA_CONTACTO = re.compile(r"^\[(CORREO|TEL)_\d{1,2}\]$")


def _texto(valor, nombre: str, maximo: int, obligatorio: bool = True, minimo: int = 1) -> str | None:
    """Limpia un texto y aplica su largo. Recibe valor, nombre del campo, maximo, si es obligatorio y minimo."""
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        if obligatorio:
            raise ArgumentoInvalido(f"falta {nombre}")
        return None
    if not isinstance(valor, str):
        raise ArgumentoInvalido(f"{nombre} debe ser texto")
    limpio = " ".join(_CONTROL.sub(" ", valor).split())
    if len(limpio) < minimo:
        raise ArgumentoInvalido(f"{nombre} es muy corto")
    return limpio[:maximo]


def _marca(valor, nombre: str, patron: re.Pattern, obligatorio: bool) -> str | None:
    """Acepta solo una marca de seudonimo ([CORREO_1], [TEL_1]). Recibe valor, nombre, patron y si es obligatorio."""
    limpio = _texto(valor, nombre, 20, obligatorio)
    if limpio is None:
        return None
    if not patron.match(limpio):
        raise ArgumentoInvalido(f"{nombre} debe ser la marca que aparece en la conversación (p. ej. [CORREO_1])")
    return limpio


def _codigo(valor) -> str:
    """Valida y normaliza un codigo de pedido. Recibe el valor."""
    codigo = codigo_valido(valor if isinstance(valor, str) else "")
    if not codigo:
        raise ArgumentoInvalido("el código del pedido no es válido")
    return codigo


def validar_argumentos(nombre: str, argumentos: dict) -> dict:
    """Valida y limpia los argumentos de una funcion. Recibe el nombre y los argumentos crudos."""
    if nombre not in NOMBRES:
        raise ArgumentoInvalido("función no disponible")
    if not isinstance(argumentos, dict):
        raise ArgumentoInvalido("los argumentos deben ser un objeto")
    a = argumentos
    if nombre == "buscar_conocimiento":
        return {"consulta": _texto(a.get("consulta"), "la consulta", 200)}
    if nombre == "rastrear_pedido":
        return {"codigo": _codigo(a.get("codigo"))}
    if nombre == "reprogramar_entrega":
        return {"codigo": _codigo(a.get("codigo")), "franja": _texto(a.get("franja"), "la franja", 80)}
    if nombre == "registrar_contacto":
        volumen = a.get("volumen_diario")
        if volumen is not None:
            try:
                volumen = int(volumen)
            except (TypeError, ValueError):
                raise ArgumentoInvalido("el volumen debe ser un número")
            if not 0 <= volumen <= 1_000_000:
                raise ArgumentoInvalido("el volumen está fuera de rango")
        return {
            "nombre": _texto(a.get("nombre"), "el nombre", 120, minimo=2),
            "empresa": _texto(a.get("empresa"), "la empresa", 120, obligatorio=False),
            "correo": _marca(a.get("correo"), "el correo", _RE_MARCA_CORREO, True),
            "telefono": _marca(a.get("telefono"), "el teléfono", _RE_MARCA_TEL, False),
            "volumen_diario": volumen,
            "necesidad": _texto(a.get("necesidad"), "la necesidad", 500, obligatorio=False),
        }
    if nombre == "derivar_a_persona":
        return {"motivo": _texto(a.get("motivo"), "el motivo", 200),
                "contacto": _marca(a.get("contacto"), "el contacto", _RE_MARCA_CONTACTO, False)}
    raise ArgumentoInvalido("función no disponible")   # pragma: no cover
