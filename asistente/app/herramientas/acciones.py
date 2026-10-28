# Acciones con confirmacion humana (OWASP LLM06, Excessive Agency).
#
# - Lista CERRADA: solo las acciones de ACCIONES, cada una con su rol, su ruta y su cuerpo fijos.
# - El modelo solo PROPONE: las funciones que ve no escriben nada. El servidor valida los
#   argumentos y la precondicion (consultando el nucleo con GET), guarda una propuesta y arma
#   la tarjeta Confirmar/Cancelar con sus propios textos.
# - La escritura la hace solo el endpoint de confirmar (api/acciones.py), despues del clic del
#   usuario y con SU token: el nucleo vuelve a validar rol y estado.
# - Apagado (ASISTENTE_ACCIONES_ENABLED=false), estas funciones ni se le ofrecen al modelo.
import hashlib
import re
from dataclasses import dataclass

from app.core.config import settings
from app.herramientas.catalogo import ArgumentoInvalido
from app.herramientas.cliente_core import ClienteCore, NoEncontrado

_RE_CODIGO = re.compile(r"^[A-Za-z0-9._-]{1,40}$")
_MAX_RUTAS_RETORNO = 30   # rutas que se revisan para encontrar un paquete sin ruta_id


class AccionNoValida(Exception):
    """La accion no se puede proponer (precondicion o argumentos). El mensaje se le da al modelo."""


@dataclass(frozen=True)
class Accion:
    """Definicion fija de una accion: quien puede, que se le muestra al modelo y a donde escribe."""
    roles: frozenset
    descripcion: str
    parametros: dict
    requeridos: tuple
    visible: str       # como se nombra ante el usuario (el nombre interno no se muestra)
    etiqueta: str      # texto de "estado" mientras se prepara la propuesta
    ruta: str          # plantilla de la ruta de escritura (relativa a /api)


ACCIONES: dict[str, Accion] = {
    "reprogramar_pedido": Accion(
        roles=frozenset({"admin"}),
        descripcion=(
            "PROPONE reprogramar UN pedido FALLIDO (vuelve a LISTO_PARA_ENVIO y sale de su ruta). No lo ejecuta: "
            "muestra al usuario una tarjeta para que confirme. Úsala solo si el usuario lo pide en su mensaje."
        ),
        parametros={"codigo": {"type": "string", "maxLength": 40, "description": "Código exacto del pedido, ej. PD-014."}},
        requeridos=("codigo",),
        visible="reprogramación de un pedido",
        etiqueta="Preparando la propuesta de reprogramación",
        ruta="/pedidos/{pedido_id}/reprogramar",
    ),
    "resolver_observado": Accion(
        roles=frozenset({"almacen"}),
        descripcion=(
            "PROPONE resolver UN pedido OBSERVADO ya aclarado (pasa a LISTO_PARA_ENVIO). No lo ejecuta: muestra al "
            "usuario una tarjeta para que confirme. Úsala solo si el usuario lo pide en su mensaje."
        ),
        parametros={"codigo": {"type": "string", "maxLength": 40, "description": "Código exacto del pedido, ej. PD-009."}},
        requeridos=("codigo",),
        visible="resolución de un pedido observado",
        etiqueta="Preparando la propuesta para resolver el observado",
        ruta="/almacen/pedidos/{pedido_id}/resolver-observado",
    ),
    "registrar_retorno": Accion(
        roles=frozenset({"almacen"}),
        descripcion=(
            "PROPONE registrar que UN paquete fallido volvió al almacén (igual que escanearlo en Retornos). No lo "
            "ejecuta: muestra al usuario una tarjeta para que confirme. Úsala solo si el usuario lo pide en su mensaje."
        ),
        parametros={
            "codigo": {"type": "string", "maxLength": 40, "description": "Código exacto del pedido devuelto, ej. PD-014."},
            "ruta_id": {"type": "integer", "minimum": 1, "description": "Id de la ruta de retorno, si se conoce."},
        },
        requeridos=("codigo",),
        visible="registro de un retorno",
        etiqueta="Preparando la propuesta de retorno",
        ruta="/almacen/retornos/rutas/{ruta_id}/escanear",
    ),
}


def huella_sesion(token: str) -> str:
    """Huella del token de la sesion: la propuesta solo se confirma desde la misma sesion. Recibe el token."""
    return hashlib.sha256(token.encode()).hexdigest()


def activas() -> bool:
    """Dice si las acciones estan encendidas (modulo y acciones). Sin input."""
    return bool(settings.ASISTENTE_ENABLED and settings.ASISTENTE_ACCIONES_ENABLED)


def nombres_para_rol(rol: str) -> list[str]:
    """Acciones que puede proponer un rol; vacio si el interruptor esta apagado. Recibe el rol."""
    if not activas():
        return []
    return [nombre for nombre, a in ACCIONES.items() if rol in a.roles]


def herramientas_para_rol(rol: str) -> list[dict]:
    """Definiciones 'tools' de las acciones de un rol (vacio si estan apagadas). Recibe el rol."""
    salida = []
    for nombre in nombres_para_rol(rol):
        a = ACCIONES[nombre]
        propiedades = {}
        for clave, regla in a.parametros.items():
            copia = {k: v for k, v in regla.items() if k not in ("maxLength", "minimum")}
            if clave not in a.requeridos:
                copia["type"] = [copia["type"], "null"]
            propiedades[clave] = copia
        salida.append({
            "type": "function",
            "function": {
                "name": nombre,
                "description": a.descripcion,
                "parameters": {"type": "object", "properties": propiedades, "required": list(a.requeridos)},
            },
        })
    return salida


def validar_argumentos(nombre: str, argumentos: dict) -> dict:
    """Valida los argumentos de una accion con su esquema cerrado. Recibe nombre y argumentos."""
    if not isinstance(argumentos, dict):
        raise ArgumentoInvalido("Los argumentos deben ser un objeto")
    accion = ACCIONES[nombre]
    limpios: dict = {}
    codigo = argumentos.get("codigo")
    if isinstance(codigo, str) and _RE_CODIGO.match(codigo.strip()):
        limpios["codigo"] = codigo.strip().upper()
    elif codigo not in (None, ""):
        raise ArgumentoInvalido("'codigo' tiene un formato inválido")
    if "ruta_id" in accion.parametros and argumentos.get("ruta_id") not in (None, ""):
        try:
            limpios["ruta_id"] = int(argumentos["ruta_id"])
        except (TypeError, ValueError) as exc:
            raise ArgumentoInvalido("'ruta_id' debe ser un número entero") from exc
        if limpios["ruta_id"] < 1:
            raise ArgumentoInvalido("'ruta_id' es demasiado pequeño")
    for requerido in accion.requeridos:
        if requerido not in limpios:
            raise ArgumentoInvalido(f"Falta el dato '{requerido}'")
    return limpios


# ----------------------------------------------------------------------------- precondiciones

@dataclass
class Preparada:
    """Propuesta lista para guardar: objetivo resuelto por el servidor y textos de la tarjeta."""
    objetivo: dict
    titulo: str
    detalle: str


def _mismo_codigo(valor, codigo: str) -> bool:
    """Compara codigos exactos sin importar mayusculas. Recibe el valor del nucleo y el codigo pedido."""
    return isinstance(valor, str) and valor.strip().upper() == codigo


def _unico(candidatos: list, codigo: str, donde: str) -> dict:
    """Exige exactamente una coincidencia. Recibe los candidatos, el codigo y donde se busco."""
    if not candidatos:
        raise AccionNoValida(f"No encontré el pedido {codigo} {donde}.")
    if len(candidatos) > 1:
        raise AccionNoValida(f"Hay más de un pedido con el código {codigo}; revísalo en el panel.")
    return candidatos[0]


async def _preparar_reprogramar(core: ClienteCore, a: dict) -> Preparada:
    """Precondicion: el codigo existe, es unico y el pedido esta FALLIDO. Recibe cliente y argumentos."""
    codigo = a["codigo"]
    pedidos = await core.get("/pedidos/", {"busqueda": codigo, "limit": 50})
    pedido = _unico([p for p in pedidos or [] if _mismo_codigo(p.get("codigo"), codigo)], codigo, "entre los pedidos")
    if pedido.get("estado") != "FALLIDO":
        raise AccionNoValida(
            f"El pedido {codigo} está en estado {pedido.get('estado')}: solo se puede reprogramar un pedido FALLIDO."
        )
    ruta = pedido.get("ruta_nombre")
    detalle = (
        f"Pedido de {pedido.get('cliente_origen') or 'cliente sin nombre'}"
        f"{', ' + pedido['distrito'] if pedido.get('distrito') else ''}. "
        f"Pasará de FALLIDO a LISTO_PARA_ENVIO{', saldrá de la ruta ' + ruta if ruta else ''} y volverá a su zona "
        "para reasignarlo. Si tiene un reporte de falla abierto, se cerrará."
    )
    return Preparada({"pedido_id": int(pedido["id"]), "codigo": pedido["codigo"]}, f"Reprogramar {pedido['codigo']}", detalle)


async def _preparar_resolver(core: ClienteCore, a: dict) -> Preparada:
    """Precondicion: el pedido esta en la lista de OBSERVADO y es unico. Recibe cliente y argumentos."""
    codigo = a["codigo"]
    observados = await core.get("/almacen/observados")
    item = _unico([o for o in observados or [] if _mismo_codigo(o.get("codigo"), codigo)], codigo,
                  "entre los pedidos OBSERVADO (solo se resuelve un pedido en ese estado)")
    lote = f", lote {item['lote']}" if item.get("lote") else ""
    dias = item.get("dias")
    detalle = (
        f"Pedido de {item.get('cliente') or 'cliente sin nombre'}{lote}"
        f"{f', observado hace {dias} día(s)' if dias is not None else ''}. "
        "Pasará de OBSERVADO a LISTO_PARA_ENVIO. Confírmalo solo si ya aclaraste la discrepancia."
    )
    return Preparada({"pedido_id": int(item["pedido_id"]), "codigo": item["codigo"]}, f"Resolver observado {item['codigo']}", detalle)


async def _preparar_retorno(core: ClienteCore, a: dict) -> Preparada:
    """Precondicion: el paquete es un FALLIDO de una ruta de retorno y aun no volvio. Recibe cliente y argumentos."""
    codigo = a["codigo"]
    if a.get("ruta_id"):
        try:
            rutas = [await core.get(f"/almacen/retornos/rutas/{a['ruta_id']}")]
        except NoEncontrado:
            raise AccionNoValida(f"No existe la ruta de retorno {a['ruta_id']}.")
    else:
        lista = await core.get("/almacen/retornos/rutas") or []
        con_faltantes = [r for r in lista if (r.get("conteo") or {}).get("faltantes", 1)][:_MAX_RUTAS_RETORNO]
        rutas = [await core.get(f"/almacen/retornos/rutas/{int(r['ruta_id'])}") for r in con_faltantes]
    encontrados = [
        (r, f) for r in rutas for f in (r.get("fallidos") or []) if _mismo_codigo(f.get("codigo"), codigo)
    ]
    ruta, fallido = _unico(encontrados, codigo, "entre los paquetes fallidos por retornar")
    if fallido.get("retornado_en"):
        raise AccionNoValida(f"El paquete {codigo} ya fue registrado como retornado.")
    detalle = (
        f"Paquete de {fallido.get('cliente_origen') or 'cliente sin nombre'} en la ruta {ruta.get('nombre') or ruta.get('ruta_id')}. "
        "Quedará registrado como devuelto al almacén, igual que al escanearlo en Retornos de ruta."
    )
    objetivo = {"ruta_id": int(ruta["ruta_id"]), "codigo": fallido["codigo"], "pedido_id": fallido.get("pedido_id")}
    return Preparada(objetivo, f"Registrar retorno de {fallido['codigo']}", detalle)


_PREPARAR = {
    "reprogramar_pedido": _preparar_reprogramar,
    "resolver_observado": _preparar_resolver,
    "registrar_retorno": _preparar_retorno,
}


async def preparar(nombre: str, core: ClienteCore, argumentos: dict) -> Preparada:
    """Valida la precondicion de una accion consultando el nucleo (solo GET). Recibe nombre, cliente y argumentos."""
    return await _PREPARAR[nombre](core, argumentos)


# ----------------------------------------------------------------------------- ejecucion (solo tras el clic)

def ruta_y_cuerpo(nombre: str, objetivo: dict) -> tuple[str, dict | None]:
    """Arma la ruta y el cuerpo de la escritura desde ACCIONES y el objetivo guardado. Recibe nombre y objetivo."""
    accion = ACCIONES[nombre]
    if nombre == "registrar_retorno":
        return accion.ruta.format(ruta_id=int(objetivo["ruta_id"])), {"codigo": str(objetivo["codigo"])[:40]}
    return accion.ruta.format(pedido_id=int(objetivo["pedido_id"])), None


async def ejecutar(nombre: str, objetivo: dict, core: ClienteCore) -> tuple[bool, str]:
    """Hace la escritura con el token del usuario. Devuelve (salio bien, mensaje). Recibe nombre, objetivo y cliente.
    Los errores del nucleo (Rechazado, SinPermiso, ...) se propagan para que el endpoint los traduzca."""
    ruta, cuerpo = ruta_y_cuerpo(nombre, objetivo)
    respuesta = await core.post_accion(ruta, cuerpo) or {}
    mensaje = str(respuesta.get("mensaje") or "Listo.")[:300]
    if nombre == "registrar_retorno" and respuesta.get("resultado") != "RETORNADO":
        return False, mensaje
    return True, mensaje
