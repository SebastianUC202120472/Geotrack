# Lista CERRADA de funciones de consulta que el modelo puede pedir.
# - Ninguna crea, edita ni borra datos: todas leen la API del nucleo con GET.
# - El modelo no escribe SQL ni direcciones: solo elige una funcion y sus filtros,
#   y cada argumento se valida contra el esquema antes de ejecutarse.
# - Cada rol recibe solo las funciones cuyos datos ve en el panel.
import re
import unicodedata
from datetime import date


def sin_tildes(texto: str) -> str:
    """Quita tildes y diéresis de un texto (para comparar sin importar acentos). Recibe el texto."""
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")

ESTADOS_PEDIDO = [
    "POR_RECOGER", "RECOGIDO", "OBSERVADO", "LISTO_PARA_ENVIO", "GEOCODIFICACION_FALLIDA",
    "ASIGNADO", "EN_RUTA", "ENTREGADO", "FALLIDO", "CANCELADO", "NO_REALIZADO",
]

_PRESENTAR = {
    "type": "string",
    "enum": ["texto", "tabla", "grafico"],
    "description": "Cómo mostrar el resultado en el chat. Usa 'tabla' o 'grafico' solo si el usuario lo pide o ayuda a leer muchos datos.",
}
_FECHA = {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}$", "description": "Fecha AAAA-MM-DD (hora de Lima)."}
_TEXTO_CORTO = {"type": "string", "maxLength": 80}

DEFINICIONES = {
    "resumen_del_dia": {
        "descripcion": "Resumen de la operación de HOY: entregados, fallidos, pendientes, rutas activas, auxilios y reportes abiertos (para almacén: recojos, observados y retornos). Úsala para '¿cómo vamos hoy?' o 'resumen del día'.",
        "parametros": {},
        "roles": {"admin", "almacen"},
    },
    "buscar_pedidos": {
        "descripcion": "Busca y cuenta pedidos con filtros (código, cliente, DNI del destinatario, distrito, estado y fechas). Devuelve el total, el conteo por estado, una agrupación opcional y una muestra de pedidos.",
        "parametros": {
            "codigo": {**_TEXTO_CORTO, "description": "Código del pedido, ej. PD-001, o referencia del cliente."},
            "cliente": {**_TEXTO_CORTO, "description": "Empresa cliente de origen, ej. Ripley."},
            "dni": {"type": "string", "maxLength": 20, "description": "DNI del destinatario tal como lo escribió el usuario (puede ser una marca [DNI_1])."},
            "distrito": {**_TEXTO_CORTO, "description": "Distrito de destino, ej. Santiago de Surco."},
            "texto": {**_TEXTO_CORTO, "description": "Texto libre para buscar en código, cliente, dirección o distrito."},
            "estado": {"type": "string", "enum": ESTADOS_PEDIDO},
            "desde": _FECHA,
            "hasta": _FECHA,
            "fecha_de": {
                "type": "string",
                "enum": ["creacion", "entrega"],
                "description": "Qué fecha filtrar. Por defecto: 'entrega' para ENTREGADO y 'creacion' para lo demás.",
            },
            "agrupar_por": {"type": "string", "enum": ["estado", "distrito", "cliente", "dia"]},
            "presentar": _PRESENTAR,
        },
        "roles": {"admin"},
    },
    "trazabilidad_pedido": {
        "descripcion": "Línea de tiempo completa de UN pedido por su código: estados, ruta, conductor, motivo de fallo y quién hizo cada cambio.",
        "parametros": {
            "codigo": {**_TEXTO_CORTO, "description": "Código del pedido, ej. PD-001."},
            "presentar": _PRESENTAR,
        },
        "requeridos": ["codigo"],
        "roles": {"admin"},
    },
    "estado_rutas": {
        "descripcion": "Rutas de reparto con su conductor, vehículo y avance (entregadas, fallidas, pendientes).",
        "parametros": {
            "nombre": {**_TEXTO_CORTO, "description": "Parte del nombre de la ruta, ej. Miraflores."},
            "conductor": {**_TEXTO_CORTO, "description": "Nombre del conductor."},
            "solo_activas": {"type": "boolean", "description": "true (por defecto) para ver solo rutas en curso."},
            "presentar": _PRESENTAR,
        },
        "roles": {"admin"},
    },
    "ubicacion_conductores": {
        "descripcion": "Última ubicación conocida de los conductores (zona aproximada, hace cuánto se reportó, ruta y paradas pendientes). Úsala para '¿dónde está Juan?'.",
        "parametros": {
            "nombre": {**_TEXTO_CORTO, "description": "Nombre (o parte) del conductor. Vacío = todos."},
            "presentar": _PRESENTAR,
        },
        "roles": {"admin", "almacen"},
    },
    "auxilios_mecanicos": {
        "descripcion": "Auxilios mecánicos (averías reportadas por conductores) con su ruta, vehículo y si ya se mandó ayuda.",
        "parametros": {
            "estado": {"type": "string", "enum": ["ABIERTA", "RESUELTA", "TODAS"], "description": "Por defecto ABIERTA."},
            "conductor": _TEXTO_CORTO,
            "presentar": _PRESENTAR,
        },
        "roles": {"admin"},
    },
    "reportes_falla": {
        "descripcion": "Reportes de falla de pedidos enviados por los conductores (motivo, descripción y respuesta).",
        "parametros": {
            "estado": {"type": "string", "enum": ["ABIERTO", "RESUELTO", "TODOS"], "description": "Por defecto ABIERTO."},
            "pedido": {**_TEXTO_CORTO, "description": "Código del pedido."},
            "presentar": _PRESENTAR,
        },
        "roles": {"admin"},
    },
    "solicitudes_bandeja": {
        "descripcion": "Solicitudes de la Bandeja de correos (clientes que piden recojos). Sin conversacion_id lista las conversaciones; con conversacion_id trae un extracto de sus últimos mensajes.",
        "parametros": {
            "estado": {"type": "string", "enum": ["PENDIENTE", "ATENDIDA", "TODAS"], "description": "Por defecto PENDIENTE."},
            "conversacion_id": {"type": "integer", "minimum": 1},
            "presentar": _PRESENTAR,
        },
        "roles": {"admin"},
    },
    "retornos_almacen": {
        "descripcion": "Retornos al almacén: rutas con pedidos fallidos y cuántos paquetes ya volvieron o faltan. Con ruta_id trae el detalle.",
        "parametros": {
            "ruta_id": {"type": "integer", "minimum": 1},
            "presentar": _PRESENTAR,
        },
        "roles": {"admin", "almacen"},
    },
    "pedidos_observados": {
        "descripcion": "Pedidos OBSERVADO (faltantes en el ingreso al almacén) con su lote y días que llevan observados.",
        "parametros": {"cliente": _TEXTO_CORTO, "presentar": _PRESENTAR},
        "roles": {"admin", "almacen"},
    },
    "recojos_almacen": {
        "descripcion": "Solicitudes de recojo en el almacén con su conciliación (esperados, listos, observados, por recoger).",
        "parametros": {
            "estado": {**_TEXTO_CORTO, "description": "Estado del recojo, ej. SOLICITADO, EN_RUTA, RECOGIDO, INGRESADO."},
            "cliente": _TEXTO_CORTO,
            "presentar": _PRESENTAR,
        },
        "roles": {"admin", "almacen"},
    },
    "avance_por_cliente": {
        "descripcion": "Avance acumulado de los pedidos de cada empresa cliente: total, entregados, fallidos, en proceso y pendientes.",
        "parametros": {"cliente": _TEXTO_CORTO, "presentar": _PRESENTAR},
        "roles": {"admin"},
    },
}

# Texto que ve el usuario mientras se ejecuta cada funcion.
ETIQUETAS = {
    "resumen_del_dia": "Armando el resumen del día",
    "buscar_pedidos": "Consultando pedidos",
    "trazabilidad_pedido": "Revisando la trazabilidad del pedido",
    "estado_rutas": "Revisando las rutas",
    "ubicacion_conductores": "Buscando la ubicación de los conductores",
    "auxilios_mecanicos": "Revisando auxilios mecánicos",
    "reportes_falla": "Revisando reportes de falla",
    "solicitudes_bandeja": "Revisando la Bandeja",
    "retornos_almacen": "Revisando retornos al almacén",
    "pedidos_observados": "Revisando pedidos observados",
    "recojos_almacen": "Revisando recojos",
    "avance_por_cliente": "Calculando el avance por cliente",
}


def nombres_para_rol(rol: str) -> list[str]:
    """Funciones que puede usar un rol del panel. Recibe el rol."""
    return [nombre for nombre, d in DEFINICIONES.items() if rol in d["roles"]]


# Reglas que valida el servidor (validar_argumentos) y que no hace falta mandarle al modelo:
# se repiten en casi todas las funciones y solo gastan tokens de cada pregunta.
_SOLO_SERVIDOR = ("maxLength", "minimum", "pattern")


def _para_modelo(regla: dict, requerido: bool) -> dict:
    """Version compacta de la regla que se envia al modelo. Recibe la regla y si es obligatoria.
    - Sin las restricciones que ya valida el servidor.
    - 'presentar' sin descripcion: su uso se explica una sola vez en las instrucciones.
    - Los filtros opcionales admiten null: algunos modelos (gpt-oss en Groq) mandan null en los
      que no usan y Groq rechaza la llamada si el esquema no lo permite."""
    copia = {k: v for k, v in regla.items() if k not in _SOLO_SERVIDOR}
    if regla is _PRESENTAR:
        copia.pop("description", None)
    if not requerido:
        if isinstance(copia.get("type"), str):
            copia["type"] = [copia["type"], "null"]
        if "enum" in copia:
            copia["enum"] = [*copia["enum"], None]
    return copia


def herramientas_para_rol(rol: str) -> list[dict]:
    """Definiciones en formato 'tools' (compatible OpenAI) para un rol, en version compacta.
    Recibe el rol. Solo incluye las funciones de ese rol; validar_argumentos aplica las reglas completas."""
    salida = []
    for nombre in nombres_para_rol(rol):
        d = DEFINICIONES[nombre]
        requeridos = d.get("requeridos", [])
        salida.append({
            "type": "function",
            "function": {
                "name": nombre,
                "description": d["descripcion"],
                "parameters": {
                    "type": "object",
                    "properties": {
                        clave: _para_modelo(regla, clave in requeridos)
                        for clave, regla in d["parametros"].items()
                    },
                    "required": requeridos,
                },
            },
        })
    return salida


class ArgumentoInvalido(ValueError):
    """Un argumento no cumple el esquema de la funcion."""


def validar_argumentos(nombre: str, argumentos: dict) -> dict:
    """Valida y limpia los argumentos segun el esquema; descarta claves desconocidas. Recibe nombre y argumentos."""
    if not isinstance(argumentos, dict):
        raise ArgumentoInvalido("Los argumentos deben ser un objeto")
    definicion = DEFINICIONES[nombre]
    esquema = definicion["parametros"]
    limpios = {}
    for clave, valor in argumentos.items():
        if clave not in esquema or valor is None or valor == "":
            continue
        limpios[clave] = _validar_valor(clave, valor, esquema[clave])
    for requerido in definicion.get("requeridos", []):
        if requerido not in limpios:
            raise ArgumentoInvalido(f"Falta el dato '{requerido}'")
    return limpios


def _validar_valor(clave: str, valor, regla: dict):
    """Valida un valor contra su regla (tipo, enum, largo, patron). Recibe clave, valor y regla."""
    tipo = regla.get("type")
    if tipo == "string":
        if not isinstance(valor, (str, int, float)):
            raise ArgumentoInvalido(f"'{clave}' debe ser texto")
        valor = str(valor).strip()
        if "enum" in regla:
            valor = sin_tildes(valor).replace(" ", "_")
            valor = valor.upper() if regla["enum"][0].isupper() else valor.lower()
            if valor not in regla["enum"]:
                raise ArgumentoInvalido(f"'{clave}' debe ser uno de: {', '.join(regla['enum'])}")
        if "pattern" in regla:
            if not re.match(regla["pattern"], valor):
                raise ArgumentoInvalido(f"'{clave}' tiene un formato inválido")
            if regla.get("pattern") == _FECHA["pattern"]:
                try:
                    date.fromisoformat(valor)
                except ValueError as exc:
                    raise ArgumentoInvalido(f"'{clave}' no es una fecha válida") from exc
        return valor[: regla.get("maxLength", 80)]
    if tipo == "integer":
        try:
            entero = int(valor)
        except (TypeError, ValueError) as exc:
            raise ArgumentoInvalido(f"'{clave}' debe ser un número entero") from exc
        if entero < regla.get("minimum", entero):
            raise ArgumentoInvalido(f"'{clave}' es demasiado pequeño")
        return entero
    if tipo == "boolean":
        if isinstance(valor, bool):
            return valor
        if str(valor).lower() in ("true", "1", "si", "sí"):
            return True
        if str(valor).lower() in ("false", "0", "no"):
            return False
        raise ArgumentoInvalido(f"'{clave}' debe ser verdadero o falso")
    raise ArgumentoInvalido(f"'{clave}' no es un dato admitido")
