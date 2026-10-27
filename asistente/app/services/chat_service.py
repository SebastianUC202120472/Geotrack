# Orquesta un turno de conversacion:
#   1. arma el contexto (instrucciones + memoria de la conversacion + pregunta),
#   2. deja que el modelo elija funciones de la lista cerrada de su rol,
#   3. ejecuta cada funcion contra la API del nucleo con el token del usuario,
#   4. devuelve al modelo los datos enmascarados y delimitados,
#   5. transmite la respuesta mientras se escribe, con sus tablas, graficos y enlaces,
#   6. guarda el historial y la auditoria (quien pregunto que y que se ejecuto).
import json
import time
from typing import AsyncIterator

import httpx
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.core.registro import log
from app.herramientas.catalogo import (
    ETIQUETAS,
    NOMBRES_VISIBLES,
    ArgumentoInvalido,
    herramientas_para_rol,
    nombres_para_rol,
    validar_argumentos,
)
from app.herramientas.cliente_core import ClienteCore, ErrorCore, NoEncontrado, SesionInvalida, SinPermiso
from app.herramientas.funciones import FUNCIONES, Contexto
from app.ia.prompt import envolver_datos, instrucciones_sistema
from app.ia.proveedores import CadenaProveedores, ErrorProveedor, SinProveedores
from app.repositories import auditoria_repository, conversacion_repository
from app.services.defensa import AVISO_DATOS, AVISO_USUARIO, intenta_cambiar_reglas, neutralizar_datos
from app.services.privacidad import FiltroSalida, FiltroTablas, RestituidorFlujo, Seudonimos, enmascarar_texto, sanear_datos

_MAX_LLAMADAS_POR_RONDA = 4
# Lo que ve el usuario cuando ningun proveedor de IA responde (el detalle tecnico va al log).
MENSAJE_SATURADO = "El asistente está saturado, intenta en unos segundos."


def _evento(tipo: str, **datos) -> dict:
    """Arma un evento para el navegador. Recibe el tipo y sus datos."""
    return {"tipo": tipo, **datos}


def _resumen_consultas(mensajes_previos: list) -> str:
    """Describe las consultas de turnos anteriores para que el modelo recuerde los filtros. Recibe los mensajes."""
    lineas = []
    for m in mensajes_previos:
        for c in (m.consultas or []):
            argumentos = json.dumps(c.get("argumentos") or {}, ensure_ascii=False)
            lineas.append(f"- {c.get('nombre')} {argumentos}")
    if not lineas:
        return ""
    return "\n\nConsultas que ya hiciste en esta conversación (de la más antigua a la más reciente):\n" + "\n".join(lineas[-10:])


def _construir_mensajes(usuario: dict, previos: list, pregunta: str, seud: Seudonimos) -> list[dict]:
    """Arma la lista de mensajes para el modelo con la memoria de la sesion. Recibe usuario, mensajes previos, pregunta y seudonimos."""
    sistema = instrucciones_sistema(usuario.get("nombre") or usuario.get("correo", ""), usuario["rol"])
    sistema += seud.ocultar(_resumen_consultas(previos))
    mensajes = [{"role": "system", "content": sistema}]
    for m in previos:
        if m.contenido:
            mensajes.append({
                "role": "user" if m.rol == "usuario" else "assistant",
                "content": seud.ocultar(m.contenido),
            })
    contenido = seud.ocultar(pregunta)
    if intenta_cambiar_reglas(pregunta):
        contenido += AVISO_USUARIO
    mensajes.append({"role": "user", "content": contenido})
    return mensajes


def _argumentos_para_auditoria(argumentos: dict) -> dict:
    """Copia de los argumentos con DNI y telefonos enmascarados. Recibe los argumentos."""
    return {k: enmascarar_texto(v) if isinstance(v, str) else v for k, v in argumentos.items()}


async def _ejecutar_llamada(llamada: dict, rol: str, contexto: Contexto, seud: Seudonimos) -> tuple[dict, list, dict]:
    """Ejecuta una llamada del modelo de forma segura. Recibe la llamada, rol, contexto y seudonimos.
    Devuelve (datos para el modelo, bloques para el widget, registro de auditoria)."""
    nombre = llamada["function"]["name"]
    registro = {"nombre": nombre, "argumentos": {}, "ok": False}

    if nombre not in nombres_para_rol(rol) or nombre not in FUNCIONES:
        return {"error": "Esa consulta no está disponible para este usuario."}, [], registro
    try:
        crudos = json.loads(llamada["function"].get("arguments") or "{}")
        argumentos = validar_argumentos(nombre, seud.restituir_argumentos(crudos))
    except (ValueError, ArgumentoInvalido) as exc:
        return {"error": f"Argumentos inválidos: {exc}"}, [], registro

    registro["argumentos"] = _argumentos_para_auditoria(argumentos)
    try:
        resultado = await FUNCIONES[nombre](contexto, argumentos)
    except SesionInvalida:
        raise
    except SinPermiso:
        return {"error": "El rol del usuario no tiene acceso a este dato en el panel."}, [], registro
    except NoEncontrado as exc:
        return {"error": f"No encontrado: {exc}"}, [], registro
    except ErrorCore as exc:
        log.warning("Consulta %s fallo: %s", nombre, exc)
        return {"error": "No se pudo consultar el sistema en este momento."}, [], registro

    registro["ok"] = "error" not in resultado.datos
    bloques = [sanear_datos(b, max_texto=120) if b.get("tipo") == "tabla" else b for b in resultado.bloques]
    # El texto de terceros con ordenes para el asistente no llega al modelo (OWASP LLM01).
    datos, omitio = neutralizar_datos(sanear_datos(resultado.datos))
    if omitio:
        registro["texto_omitido"] = True
        if isinstance(datos, dict):
            datos["aviso_seguridad"] = AVISO_DATOS
    return datos, bloques, registro


async def conversar(
    db: Session,
    usuario: dict,
    token: str,
    pregunta: str,
    conversacion_id: str | None,
    origen: str,
    cadena: CadenaProveedores,
    http_ia: httpx.AsyncClient,
    http_core: httpx.AsyncClient | None = None,
) -> AsyncIterator[dict]:
    """Ejecuta un turno completo y emite eventos (inicio, estado, texto, bloque, fin, error). Recibe sesion, usuario, token, pregunta y dependencias."""
    inicio_ms = time.monotonic()
    rol = usuario["rol"]
    consultas: list[dict] = []
    proveedor_usado = None
    resultado_auditoria = "error"

    conversacion = None
    if conversacion_id:
        conversacion = await run_in_threadpool(conversacion_repository.obtener_del_usuario, db, conversacion_id, usuario["id"])
    if conversacion is None:
        conversacion = await run_in_threadpool(conversacion_repository.crear, db, usuario["id"], enmascarar_texto(pregunta)[:60])
    previos = await run_in_threadpool(
        conversacion_repository.ultimos_mensajes, db, conversacion.id, settings.ASISTENTE_TURNOS_MEMORIA
    )
    await run_in_threadpool(conversacion_repository.agregar_mensaje, db, conversacion, "usuario", pregunta, origen)
    yield _evento("inicio", conversacion_id=conversacion.id, titulo=conversacion.titulo)

    seud = Seudonimos()
    mensajes = _construir_mensajes(usuario, previos, pregunta, seud)
    herramientas = herramientas_para_rol(rol)
    contexto = Contexto(core=ClienteCore(token, http_core), rol=rol)
    texto_visible = ""
    bloques: list[dict] = []
    rutas_enlazadas: set[str] = set()

    try:
        for ronda in range(settings.ASISTENTE_MAX_RONDAS_FUNCIONES + 1):
            llamadas: list[dict] = []
            texto_ronda = ""
            restituidor = RestituidorFlujo(seud)
            filtro = FiltroSalida(NOMBRES_VISIBLES)
            # Respaldo de la regla del prompt: las tablas Markdown del texto se quitan (el detalle va en la tabla del servidor).
            tablas = FiltroTablas()
            # Si una ronda anterior ya escribio texto, la siguiente empieza en otro parrafo.
            separador_pendiente = bool(texto_visible) and not texto_visible.endswith("\n")

            async for tipo, valor in cadena.transmitir(mensajes, herramientas, http_ia):
                if tipo == "proveedor":
                    proveedor_usado = valor
                elif tipo == "texto":
                    texto_ronda += valor
                    visible = tablas.agregar(filtro.agregar(restituidor.agregar(valor)))
                    if visible:
                        if separador_pendiente:
                            visible = "\n\n" + visible
                            separador_pendiente = False
                        texto_visible += visible
                        yield _evento("texto", texto=visible)
                elif tipo == "llamadas":
                    llamadas = valor
            resto = tablas.agregar(filtro.agregar(restituidor.cerrar()) + filtro.cerrar()) + tablas.cerrar()
            if tablas.quito_tabla:
                log.info("Se quitó una tabla Markdown del texto del modelo")
            if resto:
                if separador_pendiente:
                    resto = "\n\n" + resto
                    separador_pendiente = False
                texto_visible += resto
                yield _evento("texto", texto=resto)

            if not llamadas:
                break
            if ronda == settings.ASISTENTE_MAX_RONDAS_FUNCIONES:
                aviso = "\n\nNo pude completar la consulta con los pasos permitidos. ¿Puedes hacerla más específica?"
                texto_visible += aviso
                yield _evento("texto", texto=aviso)
                break

            mensajes.append({"role": "assistant", "content": texto_ronda or None, "tool_calls": llamadas})
            for indice, llamada in enumerate(llamadas):
                if indice >= _MAX_LLAMADAS_POR_RONDA:
                    datos, nuevos, registro = {"error": "Demasiadas consultas a la vez; pide menos datos."}, [], None
                else:
                    nombre = llamada["function"]["name"]
                    yield _evento("estado", texto=ETIQUETAS.get(nombre, "Consultando el sistema") + "…")
                    datos, nuevos, registro = await _ejecutar_llamada(llamada, rol, contexto, seud)
                if registro:
                    consultas.append(registro)
                for bloque in nuevos:
                    if bloque.get("tipo") == "enlace":
                        if bloque["ruta"] in rutas_enlazadas:
                            continue
                        rutas_enlazadas.add(bloque["ruta"])
                    bloques.append(bloque)
                    yield _evento("bloque", bloque=bloque)
                mensajes.append({
                    "role": "tool",
                    "tool_call_id": llamada["id"],
                    "name": llamada["function"]["name"],
                    "content": envolver_datos(llamada["function"]["name"], datos),
                })

        if not texto_visible.strip() and not bloques:
            texto_visible = "No pude generar una respuesta. ¿Puedes reformular la pregunta?"
            yield _evento("texto", texto=texto_visible)

        mensaje = await run_in_threadpool(
            conversacion_repository.agregar_mensaje, db, conversacion, "asistente", texto_visible, "texto", bloques, consultas
        )
        resultado_auditoria = "ok"
        yield _evento("fin", mensaje_id=mensaje.id, conversacion_id=conversacion.id)
    except SesionInvalida:
        resultado_auditoria = "rechazado"
        yield _evento("error", codigo=401, texto="Tu sesión expiró. Vuelve a iniciar sesión.")
    except SinProveedores as exc:
        log.warning("Sin proveedores de IA: %s", exc)
        yield _evento("error", codigo=503, texto=MENSAJE_SATURADO)
    except ErrorProveedor as exc:
        log.warning("La respuesta se corto a mitad: %s", exc)
        yield _evento("error", codigo=503, texto="La respuesta se interrumpió. Vuelve a preguntar, por favor.")
    except Exception:
        log.exception("Error inesperado en el asistente")
        yield _evento("error", codigo=500, texto="Ocurrió un error al responder. Inténtalo de nuevo.")
    finally:
        await run_in_threadpool(
            auditoria_repository.registrar,
            db,
            usuario_id=usuario["id"],
            usuario_correo=usuario.get("correo", ""),
            rol=rol,
            conversacion_id=conversacion.id,
            origen=origen,
            pregunta=enmascarar_texto(pregunta)[:2000],
            funciones=consultas,
            proveedor=proveedor_usado,
            resultado=resultado_auditoria,
            duracion_ms=int((time.monotonic() - inicio_ms) * 1000),
        )
