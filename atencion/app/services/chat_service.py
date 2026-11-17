# Orquesta un turno de la conversacion de atencion:
#   1. detecta el idioma; cambia correos y telefonos por marcas y oculta DNI y digitos del DNI;
#      revisa si el mensaje intenta cambiar las reglas,
#   2. recupera de la base de conocimiento los articulos que responden la pregunta (RAG),
#   3. arma el contexto (instrucciones + articulos como datos + memoria corta de la conversacion),
#   4. deja que el modelo use la lista cerrada de funciones (portal) y transmite la respuesta filtrada,
#      junto con los eventos del widget (formulario de DNI, tarjetas de confirmacion, derivacion),
#   5. si no hay IA disponible (cuota, caida o tope diario) responde con la base de conocimiento,
#   6. si el visitante sigue sin respuesta util, le ofrece hablar con una persona,
#   7. guarda ambos mensajes, ya enmascarados, en las tablas propias.
import json
import re
from typing import AsyncIterator

import httpx
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.conocimiento.buscador import Resultado, indice
from app.core.config import settings
from app.core.registro import log
from app.herramientas import funciones
from app.herramientas.catalogo import HERRAMIENTAS, NOMBRES, ArgumentoInvalido, validar_argumentos
from app.herramientas.cliente_portal import ClientePortal, codigo_valido
from app.ia.prompt import envolver_datos, instrucciones_sistema
from app.ia.proveedores import CadenaProveedores, ErrorProveedor, SinProveedores
from app.models.conversacion import Conversacion
from app.repositories import conversacion_repository as repo
from app.services import idioma as servicio_idioma
from app.services.defensa import (
    AVISO_USUARIO, MENSAJE_OMITIDO, frases_para_no_repetir, intenta_cambiar_reglas, neutralizar_datos,
)
from app.services.privacidad import enmascarar_texto
from app.services.salida import FiltroSalida, sanear
from app.services.sesion import sesiones

_MAX_LLAMADAS_POR_RONDA = 3
_CONTACTO = "WhatsApp +51 922 507 593"
# Funciones que, si se ejecutan bien, cuentan como "el asistente pudo ayudar".
_FUNCIONES_UTILES = {"rastrear_pedido", "reprogramar_entrega", "registrar_contacto", "derivar_a_persona"}

TEXTOS = {
    "es": {
        "sin_ia_intro": "En este momento no puedo conversar con normalidad, pero esto puede ayudarte:",
        "sin_ia_nada": "En este momento no puedo responder tu consulta. Puedes rastrear tu pedido en /portal "
                       f"o escribirnos por {_CONTACTO}, de lunes a sábado.",
        "sin_ia_cierre": f"Si necesitas a una persona del equipo, escríbenos por {_CONTACTO}.",
        "seguro": "Solo puedo ayudarte con los envíos y servicios de SAVA. ¿En qué te ayudo con tu pedido o con el servicio?",
        "vacio": "No logré entender bien tu consulta. ¿Me la cuentas con otras palabras?",
        "error": "Se cortó la respuesta. Por favor, vuelve a intentarlo en unos segundos.",
    },
    "en": {
        "sin_ia_intro": "I can't chat normally right now, but this may help:",
        "sin_ia_nada": "I can't answer your question right now. You can track your order at /portal "
                       f"or write to us on {_CONTACTO}, Monday to Saturday.",
        "sin_ia_cierre": f"If you need a team member, write to us on {_CONTACTO}.",
        "seguro": "I can only help with SAVA's shipments and services. How can I help you with your order or our service?",
        "vacio": "I didn't quite understand your question. Could you tell me in other words?",
        "error": "The answer was interrupted. Please try again in a few seconds.",
    },
}


def _evento(tipo: str, **datos) -> dict:
    """Arma un evento para el navegador. Recibe el tipo y sus datos."""
    return {"tipo": tipo, **datos}


def _articulos_como_datos(resultados: list[Resultado]) -> list[dict]:
    """Articulos recuperados en el formato que recibe el modelo, sin ordenes ocultas. Recibe los resultados."""
    # Los enlaces externos se quitan antes de que el modelo los vea. Un articulo con ordenes se descarta
    # ENTERO, titulo incluido: con solo el titulo ("Promocion de envio gratis") el modelo ya inventa.
    limpios = []
    for r in resultados:
        dato = {"titulo": r.titulo, "contenido": sanear(r.contenido, settings.dominios_permitidos)}
        dato_limpio, omitio = neutralizar_datos(dato, estricto=True)
        if omitio:
            log.warning("El artículo %s/%s traía instrucciones para el asistente y se descartó", r.clave, r.idioma)
            continue
        limpios.append(dato_limpio)
    return limpios


# Codigos de pedido escritos por el visitante con el formato del nucleo (PD-001; tambien "pd 045").
_RE_CODIGO_EN_TEXTO = re.compile(r"\b(PD)[\s-]?(\d{1,10})\b", re.IGNORECASE)
NOTA_FORMULARIO = (
    "\n\n[Nota del sistema: el visitante ya tiene en pantalla el formulario para verificar el pedido {codigos} con los "
    "últimos 4 dígitos del DNI del destinatario. Si necesita el detalle, dile que lo complete ahí; no le pidas los "
    "dígitos en el chat. Puedes usar rastrear_pedido para ver el estado.]"
)


def codigos_sin_verificar(mensaje: str, estado) -> list[str]:
    """Codigos de pedido del mensaje que el visitante aun no verifico. Recibe el mensaje y el estado en memoria."""
    codigos = []
    for prefijo, numero in _RE_CODIGO_EN_TEXTO.findall(mensaje or ""):
        codigo = codigo_valido(f"{prefijo}-{numero}")
        if codigo and codigo not in codigos and not estado.token(codigo):
            codigos.append(codigo)
    return codigos[:2]


def respuesta_sin_ia(resultados: list[Resultado], idioma: str) -> str:
    """Respuesta de respaldo armada solo con la base de conocimiento. Recibe los articulos y el idioma."""
    t = TEXTOS[idioma]
    if not resultados:
        return t["sin_ia_nada"]
    partes = [t["sin_ia_intro"]]
    for r in resultados[:2]:
        partes.append(f"**{r.titulo}**\n{r.contenido}")
    partes.append(t["sin_ia_cierre"])
    return "\n\n".join(partes)


def _consulta_para_buscar(texto: str, previos: list) -> str:
    """Texto con el que se busca en la base: si el mensaje es corto ("¿y si no estoy?"), suma la
    pregunta anterior del visitante para no perder el tema. Recibe el texto y los mensajes previos."""
    if len(texto.split()) >= 6:
        return texto
    anteriores = [m.contenido for m in previos if m.rol == "usuario"]
    return f"{anteriores[-1]} {texto}" if anteriores else texto


def construir_mensajes(idioma: str, previos: list, texto: str, resultados: list[Resultado], alerta: bool) -> list[dict]:
    """Arma la lista de mensajes para el modelo. Recibe idioma, mensajes previos, texto enmascarado,
    articulos recuperados y si el mensaje intenta cambiar las reglas."""
    sistema = instrucciones_sistema(idioma)
    sistema += "\n\nBase de conocimiento relevante para esta pregunta:\n" + envolver_datos(
        "base_de_conocimiento", _articulos_como_datos(resultados) or "sin artículos relevantes")
    mensajes = [{"role": "system", "content": sistema}]
    for m in previos:
        if not m.contenido:
            continue
        if m.rol == "usuario":
            # Un mensaje que intento cambiar las reglas no vuelve a la memoria (orden plantada para despues).
            mensajes.append({"role": "user", "content": MENSAJE_OMITIDO if m.alerta_seguridad else m.contenido})
        else:
            mensajes.append({"role": "assistant", "content": m.contenido})
    mensajes.append({"role": "user", "content": texto + (AVISO_USUARIO if alerta else "")})
    return mensajes


def preparar_texto(mensaje: str, seudonimos) -> str:
    """Texto del visitante listo para el modelo y la base: correos y telefonos como marcas, DNI y
    digitos ocultos. Recibe el mensaje y los seudonimos de la conversacion."""
    return enmascarar_texto(seudonimos.ocultar(mensaje))


async def _ejecutar_llamada(llamada: dict, ctx: funciones.Contexto) -> tuple[dict, list, bool]:
    """Valida y ejecuta una funcion pedida por el modelo. Recibe la llamada y el contexto.
    Devuelve (datos para el modelo, eventos para el widget, si fue util)."""
    nombre = llamada.get("function", {}).get("name", "")
    if nombre not in NOMBRES:
        return {"error": "Esa función no existe."}, [], False
    try:
        argumentos = validar_argumentos(nombre, json.loads(llamada["function"].get("arguments") or "{}"))
    except (ValueError, ArgumentoInvalido) as exc:
        return {"error": f"Argumentos inválidos: {exc}"}, [], False
    datos, eventos = await funciones.ejecutar(nombre, argumentos, ctx)
    log.info("Función %s ejecutada (conversación %s)", nombre, ctx.conversacion.id[:8])
    return datos, eventos, nombre in _FUNCIONES_UTILES and "error" not in datos


async def conversar(
    db: Session, conversacion: Conversacion, mensaje: str, origen: str,
    cadena: CadenaProveedores, http: httpx.AsyncClient, con_ia: bool = True,
    http_core: httpx.AsyncClient | None = None, ip_visitante: str = "desconocida",
) -> AsyncIterator[dict]:
    """Atiende un mensaje del visitante y emite los eventos de la respuesta. Recibe la sesion de BD, la
    conversacion, el mensaje, su origen, la cadena de IA, el cliente http de IA, si se puede usar la IA,
    el cliente http del nucleo y la IP del visitante (para los limites del portal)."""
    estado = sesiones.de(conversacion.id)
    idioma = servicio_idioma.detectar(mensaje, conversacion.idioma)
    texto = preparar_texto(mensaje, estado.seudonimos)
    alerta = intenta_cambiar_reglas(mensaje)
    previos = await run_in_threadpool(repo.ultimos_mensajes, db, conversacion.id, settings.ATENCION_TURNOS_MEMORIA * 2)
    await run_in_threadpool(repo.agregar_mensaje, db, conversacion, "usuario", texto, origen=origen, idioma=idioma,
                            alerta_seguridad="cambio_de_reglas" if alerta else None)
    resultados = indice.buscar(_consulta_para_buscar(texto, previos), idioma, settings.ATENCION_KB_RESULTADOS,
                               settings.ATENCION_KB_PUNTAJE_MINIMO)
    claves = [r.clave for r in resultados]
    yield _evento("inicio", idioma=idioma)
    # Si el visitante escribio un codigo sin verificar, el servidor muestra el formulario de DNI y se lo
    # avisa al modelo: asi ningun modelo (ni uno chico) tiene que acordarse de no pedir los digitos.
    pendientes = codigos_sin_verificar(mensaje, estado)
    for codigo in pendientes:
        yield _evento("verificar", codigo=codigo)
    texto_modelo = texto + (NOTA_FORMULARIO.format(codigos=", ".join(pendientes)) if pendientes else "")

    ctx = funciones.Contexto(db, conversacion, estado, ClientePortal(http_core or http, ip_visitante), idioma)
    modo, proveedor, respuesta, util = "ia", None, "", bool(resultados)
    if con_ia and cadena.proveedores:
        filtro = FiltroSalida(settings.dominios_permitidos, estado.seudonimos.restituir,
                              frases_para_no_repetir(mensaje) if alerta else None)
        mensajes = construir_mensajes(idioma, previos, texto_modelo, resultados, alerta)
        emitio = False
        try:
            for ronda in range(settings.ATENCION_MAX_RONDAS_FUNCIONES + 1):
                herramientas = HERRAMIENTAS if ronda < settings.ATENCION_MAX_RONDAS_FUNCIONES else []
                llamadas = []
                async for tipo, valor in cadena.transmitir(mensajes, herramientas, http):
                    if tipo == "proveedor":
                        proveedor = valor
                    elif tipo == "texto":
                        visible = filtro.agregar(valor)
                        if visible:
                            emitio = True
                            yield _evento("texto", texto=visible)
                    elif tipo == "llamadas":
                        llamadas = valor or []
                if not llamadas or filtro.fuga:
                    break
                llamadas = llamadas[:_MAX_LLAMADAS_POR_RONDA]
                mensajes.append({"role": "assistant", "content": "", "tool_calls": llamadas})
                for llamada in llamadas:
                    datos, eventos, fue_util = await _ejecutar_llamada(llamada, ctx)
                    util = util or fue_util
                    for evento in eventos:
                        # El formulario de un codigo ya mostrado en este turno no se repite.
                        if evento.get("tipo") == "verificar":
                            if evento.get("codigo") in pendientes:
                                continue
                            pendientes.append(evento.get("codigo"))
                        yield evento
                    mensajes.append({"role": "tool", "tool_call_id": llamada["id"],
                                     "content": envolver_datos(llamada["function"]["name"], datos)})
            resto = filtro.cerrar()
            if resto:
                emitio = True
                yield _evento("texto", texto=resto)
            if filtro.fuga:
                modo = "bloqueado"
                respuesta = TEXTOS[idioma]["seguro"]
                log.warning("Respuesta descartada por fuga de instrucciones (conversación %s)", conversacion.id[:8])
                yield _evento("reemplazar", texto=respuesta)
            else:
                respuesta = filtro.texto_completo.strip()
                if not respuesta:
                    respuesta = TEXTOS[idioma]["vacio"]
                    yield _evento("texto", texto=respuesta)
        except (SinProveedores, ErrorProveedor) as exc:
            log.warning("Sin IA para responder: %s", exc)
            if emitio:
                respuesta = filtro.texto_completo.strip() + "\n\n" + TEXTOS[idioma]["error"]
                yield _evento("texto", texto="\n\n" + TEXTOS[idioma]["error"])
            else:
                con_ia = False
    else:
        con_ia = False

    if not con_ia:
        modo, proveedor = "sin_ia", None
        respuesta = respuesta_sin_ia(resultados, idioma)
        yield _evento("texto", texto=respuesta)

    # Varios mensajes seguidos sin poder ayudar (sin articulos ni funciones utiles): se ofrece una persona.
    estado.fallos_seguidos = 0 if util else estado.fallos_seguidos + 1
    if estado.fallos_seguidos >= settings.ATENCION_DERIVAR_TRAS_FALLOS and conversacion.estado != "DERIVADA":
        yield _evento("ofrecer_derivacion")

    await run_in_threadpool(repo.agregar_mensaje, db, conversacion, "asistente", enmascarar_texto(respuesta),
                            idioma=idioma, modo=modo, proveedor=proveedor, articulos=claves)
    yield _evento("fin", modo=modo)
