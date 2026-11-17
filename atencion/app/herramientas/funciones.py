# Ejecucion de las funciones que pide el modelo, contra la API publica del portal.
# Cada funcion devuelve (datos para el modelo, eventos para el widget). Los datos que vienen
# del portal pasan por una LISTA BLANCA de campos y por el enmascarado: el modelo nunca recibe
# la direccion completa, la placa, el telefono ni el nombre de quien recibio el paquete.
# Reprogramar y registrar contacto solo crean una PROPUESTA; nada se escribe hasta el clic.
import secrets
import time
from dataclasses import dataclass

from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.conocimiento.buscador import indice
from app.core.config import settings
from app.herramientas.cliente_portal import (
    Bloqueado, ClientePortal, DatosRetirados, ErrorPortal, NoEncontrado, SesionVencida,
)
from app.models.conversacion import Conversacion
from app.repositories import gestion_repository
from app.services.defensa import neutralizar_datos
from app.services.privacidad import enmascarar_texto
from app.services.salida import sanear
from app.services.sesion import EstadoConversacion, Propuesta

_MAX_EVENTOS_PEDIDO = 6
INSTRUCCION_VERIFICAR = (
    "El sistema le mostró al visitante un formulario para escribir los últimos 4 dígitos del DNI del destinatario. "
    "Pídele que lo complete ahí. NO le pidas los dígitos en el chat. Cuando verifique, vuelve a consultar el pedido."
)
NOTA_PROPUESTA = (
    "El sistema le mostró al visitante una tarjeta con Confirmar y Cancelar. Todavía NO se hizo nada: dile que revise "
    "los datos y pulse Confirmar. Nunca digas que ya quedó registrado o reprogramado."
)

TEXTOS_TARJETA = {
    "es": {"reprogramar": "Reprogramar la entrega", "contacto": "Enviar tus datos al equipo comercial",
           "pedido": "Pedido", "franja": "Nueva franja", "nombre": "Nombre", "empresa": "Empresa",
           "correo": "Correo", "telefono": "Teléfono", "volumen": "Pedidos por día", "necesidad": "Necesidad"},
    "en": {"reprogramar": "Reschedule the delivery", "contacto": "Send your details to the sales team",
           "pedido": "Order", "franja": "New time slot", "nombre": "Name", "empresa": "Company",
           "correo": "Email", "telefono": "Phone", "volumen": "Orders per day", "necesidad": "Need"},
}


@dataclass
class Contexto:
    """Lo que una funcion necesita para ejecutarse en nombre del visitante."""
    db: Session
    conversacion: Conversacion
    estado: EstadoConversacion
    portal: ClientePortal
    idioma: str


def _limpio(datos):
    """Quita ordenes ocultas y datos personales de lo que devuelve el portal. Recibe dict/lista/valor."""
    datos, _ = neutralizar_datos(datos, estricto=True)
    if isinstance(datos, dict):
        return {k: _limpio(v) for k, v in datos.items()}
    if isinstance(datos, list):
        return [_limpio(v) for v in datos]
    if isinstance(datos, str):
        return enmascarar_texto(datos)[:300]
    return datos


def detalle_para_modelo(d: dict) -> dict:
    """Detalle del pedido con solo los campos que el modelo necesita (lista blanca). Recibe el detalle del portal."""
    conductor = (d.get("conductor") or "").split()
    datos = {
        "tienda": d.get("retail"),
        "estado": d.get("estado"),
        "titulo_eta": d.get("etaT"),
        "nota": d.get("nota"),
        "parada": d.get("parada"),
        "avance": d.get("pct"),
        "motivo_intento_fallido": d.get("motivo"),
        "conductor": conductor[0] if conductor else None,
        "foto_de_entrega_disponible_en_portal": bool(d.get("podDisponible")),
        "entrega_con_registro_de_quien_recibio": bool(d.get("recibido")),
        "puede_reprogramar": bool(d.get("puedeReprogramar")),
        "reprogramacion_solicitada": d.get("reprogramacion"),
        "eventos": [{"evento": e.get("t"), "detalle": e.get("d"), "hora": e.get("h")}
                    for e in (d.get("eventos") or [])[-_MAX_EVENTOS_PEDIDO:] if isinstance(e, dict)],
    }
    return _limpio({k: v for k, v in datos.items() if v not in (None, "", [])})


def _error_portal(exc: ErrorPortal) -> dict:
    """Traduce un error del portal a un dato para el modelo. Recibe la excepcion."""
    if isinstance(exc, Bloqueado):
        return {"error": "Demasiados intentos con este pedido. Hay que esperar antes de volver a consultarlo.",
                "espera_segundos": exc.segundos}
    if isinstance(exc, DatosRetirados):
        return {"existe": True, "disponible": False,
                "nota": "Pedido antiguo: sus datos se retiraron por la política de retención y ya no se puede consultar."}
    return {"error": "El sistema de rastreo no responde en este momento. Ofrece intentar más tarde o el WhatsApp."}


async def _detalle_verificado(ctx: Contexto, codigo: str) -> dict | None:
    """Detalle del pedido si el visitante lo verifico y el token sigue vigente; si no, None. Recibe contexto y codigo."""
    token = ctx.estado.token(codigo)
    if not token:
        return None
    try:
        return await ctx.portal.detalle(codigo, token)
    except SesionVencida:
        ctx.estado.olvidar_token(codigo)
        return None


async def rastrear_pedido(ctx: Contexto, codigo: str) -> tuple[dict, list]:
    """Estado del pedido: detalle si esta verificado; si no, resumen y formulario de DNI. Recibe contexto y codigo."""
    try:
        detalle = await _detalle_verificado(ctx, codigo)
        if detalle is not None:
            datos = {"codigo": codigo, "verificado": True, "pedido": detalle_para_modelo(detalle)}
            if detalle.get("puedeReprogramar"):
                datos["franjas_para_reprogramar"] = await ctx.portal.franjas()
            return datos, []
        resumen = await ctx.portal.resumen(codigo)
    except NoEncontrado:
        return {"codigo": codigo, "existe": False,
                "nota": "No hay un pedido con ese código. Pide revisar el código (lo da la tienda)."}, []
    except ErrorPortal as exc:
        return _error_portal(exc), []
    base = {"codigo": codigo, "existe": True, "verificado": False,
            "tienda": resumen.get("retail"), "estado": resumen.get("estado")}
    if not resumen.get("tieneDni"):
        base["nota"] = "Este pedido no se puede verificar en línea. Ofrece el WhatsApp +51 922 507 593 para el detalle."
        return _limpio(base), []
    base["instruccion"] = INSTRUCCION_VERIFICAR
    return _limpio(base), [{"tipo": "verificar", "codigo": codigo}]


def _normal(texto: str) -> str:
    """Texto comparable: minusculas y espacios simples. Recibe el texto."""
    return " ".join((texto or "").lower().split())


async def _crear_propuesta(ctx: Contexto, tipo: str, datos: dict, lineas: list[str], resumen: str) -> tuple[dict, list]:
    """Guarda la propuesta (datos reales en memoria, resumen enmascarado en la base) y arma la tarjeta.
    Recibe contexto, tipo, datos, lineas visibles y resumen."""
    for ident, anterior in list(ctx.estado.propuestas.items()):
        if anterior.tipo == tipo:   # una sola propuesta pendiente por tipo: la nueva reemplaza a la anterior
            ctx.estado.propuestas.pop(ident, None)
            accion = await run_in_threadpool(gestion_repository.obtener_accion, ctx.db, ident)
            if accion and accion.estado == "PENDIENTE":
                await run_in_threadpool(gestion_repository.resolver_accion, ctx.db, accion, "VENCIDA", "reemplazada")
    ident = secrets.token_hex(16)
    ctx.estado.propuestas[ident] = Propuesta(ident, tipo, datos, time.monotonic() + settings.ATENCION_PROPUESTA_VENCE_SEG)
    await run_in_threadpool(gestion_repository.crear_accion, ctx.db, ident, ctx.conversacion.id, tipo,
                            enmascarar_texto(resumen))
    tarjeta = {"tipo": "propuesta", "id": ident, "accion": tipo, "titulo": TEXTOS_TARJETA[ctx.idioma][tipo],
               "lineas": lineas, "vence_en_seg": settings.ATENCION_PROPUESTA_VENCE_SEG}
    return {"propuesta_mostrada": True, "nota": NOTA_PROPUESTA}, [tarjeta]


def _limite_acciones(ctx: Contexto) -> dict | None:
    """Error para el modelo si la conversacion ya uso sus acciones. Recibe el contexto."""
    if ctx.estado.acciones >= settings.ATENCION_ACCIONES_POR_CONVERSACION:
        return {"error": "Esta conversación ya no puede registrar más solicitudes. Ofrece el WhatsApp +51 922 507 593."}
    return None


async def reprogramar_entrega(ctx: Contexto, codigo: str, franja: str) -> tuple[dict, list]:
    """Propone reprogramar un pedido verificado en una franja valida. Recibe contexto, codigo y franja."""
    if error := _limite_acciones(ctx):
        return error, []
    try:
        detalle = await _detalle_verificado(ctx, codigo)
        if detalle is None:
            return {"codigo": codigo, "verificado": False, "instruccion": INSTRUCCION_VERIFICAR}, \
                [{"tipo": "verificar", "codigo": codigo}]
        if not detalle.get("puedeReprogramar"):
            return {"error": "Este pedido ya no se puede reprogramar (entregado o cancelado)."}, []
        franjas = await ctx.portal.franjas()
    except ErrorPortal as exc:
        return _error_portal(exc), []
    elegida = next((f for f in franjas if _normal(f) == _normal(franja)), None)
    if elegida is None:
        return {"error": "Esa franja no está disponible. Ofrece solo estas, tal cual:", "franjas": franjas}, []
    t = TEXTOS_TARJETA[ctx.idioma]
    return await _crear_propuesta(ctx, "reprogramar", {"codigo": codigo, "franja": elegida},
                                  [f"{t['pedido']}: {codigo}", f"{t['franja']}: {elegida}"],
                                  f"reprogramar {codigo} a «{elegida}»")


async def registrar_contacto(ctx: Contexto, nombre: str, empresa: str | None, correo: str, telefono: str | None,
                             volumen_diario: int | None, necesidad: str | None) -> tuple[dict, list]:
    """Propone enviar los datos de una empresa interesada al formulario de contacto. Recibe contexto y los datos."""
    if error := _limite_acciones(ctx):
        return error, []
    seud = ctx.estado.seudonimos
    email = seud.valor(correo)
    if not email:
        return {"error": "No hay un correo con esa marca. Pide al visitante que escriba su correo."}, []
    tel = seud.valor(telefono) if telefono else None
    if telefono and not tel:
        return {"error": "No hay un teléfono con esa marca. Omite el teléfono o pídelo de nuevo."}, []
    datos = {"nombre": nombre, "empresa": empresa, "email": email, "telefono": tel, "volumen": volumen_diario,
             "mensaje": necesidad}
    t = TEXTOS_TARJETA[ctx.idioma]
    lineas = [f"{t['nombre']}: {nombre}"]
    lineas += [f"{t['empresa']}: {empresa}"] if empresa else []
    lineas += [f"{t['correo']}: {email}"]
    lineas += [f"{t['telefono']}: {tel}"] if tel else []
    lineas += [f"{t['volumen']}: {volumen_diario}"] if volumen_diario is not None else []
    lineas += [f"{t['necesidad']}: {necesidad}"] if necesidad else []
    return await _crear_propuesta(ctx, "contacto", datos, lineas,
                                  f"contacto de empresa {empresa or '(sin nombre)'}, volumen {volumen_diario or '-'}")


async def derivar_a_persona(ctx: Contexto, motivo: str, contacto: str | None, origen: str = "asistente",
                            contacto_real: str | None = None) -> tuple[dict, list]:
    """Deja la conversacion en la bandeja del equipo (una sola vez). Recibe contexto, motivo, marca de contacto
    (del modelo), origen y, si viene del formulario del widget, el contacto real."""
    existente = await run_in_threadpool(gestion_repository.derivacion_pendiente, ctx.db, ctx.conversacion.id)
    if existente:
        return {"derivada": True, "nota": "La conversación ya estaba en la bandeja del equipo."}, []
    real = contacto_real or (ctx.estado.seudonimos.valor(contacto) if contacto else None)
    await run_in_threadpool(gestion_repository.crear_derivacion, ctx.db, ctx.conversacion, origen,
                            enmascarar_texto(motivo), real, ctx.idioma)
    nota = ("La conversación quedó en la bandeja del equipo de SAVA. No es un chat en vivo: no prometas tiempos ni "
            "que alguien responderá en este chat. Dile que una persona del equipo revisará su caso"
            + (" y lo contactará por el medio que indicó." if real else
               "; si quiere que lo contacten, puede dejar su correo o teléfono, o escribir al WhatsApp +51 922 507 593."))
    return {"derivada": True, "nota": nota}, [{"tipo": "derivada"}]


def buscar_conocimiento(ctx: Contexto, consulta: str) -> tuple[dict, list]:
    """Busca en la base de conocimiento. Recibe contexto y consulta."""
    resultados = indice.buscar(consulta, ctx.idioma, settings.ATENCION_KB_RESULTADOS, settings.ATENCION_KB_PUNTAJE_MINIMO)
    articulos = [{"titulo": r.titulo, "contenido": sanear(r.contenido, settings.dominios_permitidos)} for r in resultados]
    limpio, _ = neutralizar_datos(articulos, estricto=True)
    return {"articulos": limpio or "sin resultados"}, []


async def ejecutar(nombre: str, argumentos: dict, ctx: Contexto) -> tuple[dict, list]:
    """Ejecuta una funcion de la lista cerrada con argumentos ya validados. Recibe nombre, argumentos y contexto."""
    if nombre == "buscar_conocimiento":
        return buscar_conocimiento(ctx, **argumentos)
    if nombre == "rastrear_pedido":
        return await rastrear_pedido(ctx, **argumentos)
    if nombre == "reprogramar_entrega":
        return await reprogramar_entrega(ctx, **argumentos)
    if nombre == "registrar_contacto":
        return await registrar_contacto(ctx, **argumentos)
    if nombre == "derivar_a_persona":
        return await derivar_a_persona(ctx, **argumentos)
    return {"error": "Esa función no existe."}, []
