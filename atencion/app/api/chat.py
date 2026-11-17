# Endpoints publicos del chat de atencion (landing y portal).
# Orden de los controles en cada mensaje: modulo activo -> origen del sitio -> token de la
# conversacion -> limites por IP y por conversacion -> tiempo minimo del primer mensaje ->
# tope diario global (si se alcanza, se responde sin IA con la base de conocimiento).
import json
import secrets
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.api.deps import conversacion_del_token, exigir_activo, verificar_origen
from app.conocimiento.semilla import aviso_privacidad
from app.core import tokens
from app.core.config import settings
from app.core.fechas import ahora_utc, inicio_del_dia_utc
from app.core.limites import limitador
from app.core.red import huella_ip, ip_cliente
from app.core.registro import log
from app.db.database import SessionLocal, get_db
from app.repositories import conversacion_repository as repo
from app.schemas.chat import AvisoPrivacidad, ChatRequest, ConversacionCreada, EstadoResponse, NuevaConversacion
from app.ia import transcripcion
from app.services import chat_service

router = APIRouter()

SALUDOS = {
    "es": "¡Hola! Soy el asistente virtual de SAVA. Puedo ayudarte con tu pedido, la cobertura, las "
          "reprogramaciones, los reclamos o el servicio para empresas. ¿En qué te ayudo?",
    "en": "Hi! I'm SAVA's virtual assistant. I can help you with your order, coverage, rescheduling, "
          "claims or our service for companies. How can I help you?",
}


def _huella(request: Request) -> str:
    """Huella anonima de la IP del visitante. Recibe la peticion."""
    return huella_ip(ip_cliente(request), tokens.SECRETO)


@router.get("/estado", response_model=EstadoResponse)
def estado(request: Request):
    """Dice si el chat esta activo (si no, el widget no aparece). Sin input."""
    cadena = getattr(request.app.state, "cadena", None)
    return EstadoResponse(
        activo=settings.ATENCION_ENABLED,
        con_ia=bool(settings.ATENCION_ENABLED and cadena and cadena.proveedores),
        max_caracteres=settings.ATENCION_MAX_CARACTERES,
        version_aviso=aviso_privacidad()["version"],
        voz_servidor=transcripcion.voz_en_servidor_disponible(),
        max_seg_voz=settings.ATENCION_VOZ_MAX_SEG,
    )


@router.get("/privacidad", response_model=AvisoPrivacidad, dependencies=[Depends(exigir_activo)])
def privacidad(idioma: str = Query("es", pattern="^(es|en)$")):
    """Aviso de privacidad (Ley 29733) que se muestra antes de chatear. Recibe el idioma."""
    aviso = aviso_privacidad()
    texto = aviso[idioma]
    dias = str(settings.ATENCION_RETENCION_DIAS)
    return AvisoPrivacidad(
        version=aviso["version"], titulo=texto["titulo"], resumen=texto["resumen"],
        puntos=[p.replace("{dias}", dias) for p in texto["puntos"]], aceptar=texto["aceptar"],
        enlace_politica=texto.get("enlace_politica"),
    )


@router.post("/conversaciones", response_model=ConversacionCreada, status_code=201,
             dependencies=[Depends(exigir_activo), Depends(verificar_origen)])
def nueva_conversacion(datos: NuevaConversacion, request: Request, db: Session = Depends(get_db)):
    """Abre una conversacion anonima tras aceptar el aviso de privacidad. Recibe idioma, pagina y aceptacion."""
    huella = _huella(request)
    if datos.sitio_web:
        log.info("Conversación rechazada: honeypot lleno (posible bot)")
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No se pudo iniciar la conversación")
    if not datos.acepta_privacidad or datos.version_aviso != aviso_privacidad()["version"]:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Para chatear hay que aceptar el aviso de privacidad vigente")
    if not limitador.permitir(f"conv:{huella}", settings.ATENCION_CONVERSACIONES_POR_HORA_IP, 3600):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Abriste demasiadas conversaciones. Intenta más tarde.")
    conversacion = repo.crear(db, secrets.token_hex(16), huella, datos.idioma, datos.pagina)
    return ConversacionCreada(
        token=tokens.emitir(conversacion.id),
        vence_en_seg=settings.ATENCION_CONVERSACION_VENCE_MIN * 60,
        saludo=SALUDOS[datos.idioma],
    )


def _verificar_topes(db: Session, conversacion, huella: str) -> bool:
    """Aplica los topes de la conversacion y de la IP; devuelve si aun se puede usar la IA hoy.
    Recibe la sesion, la conversacion y la huella de la IP."""
    if conversacion.mensajes_usuario >= settings.ATENCION_TURNOS_POR_CONVERSACION:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS,
                            "Esta conversación llegó a su límite de mensajes. Abre una nueva si necesitas algo más.")
    if conversacion.mensajes_usuario == 0:
        minimo = conversacion.creada_en + timedelta(seconds=settings.ATENCION_SEG_MINIMOS_PRIMER_MENSAJE)
        if ahora_utc() < minimo:
            raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Un momento, por favor, y vuelve a enviar tu mensaje.")
    hoy = inicio_del_dia_utc()
    if repo.contar_mensajes_usuario_desde(db, hoy, huella) >= settings.ATENCION_MENSAJES_POR_DIA_IP:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Llegaste al límite de mensajes de hoy. Vuelve mañana.")
    return repo.contar_mensajes_usuario_desde(db, hoy) < settings.ATENCION_TOPE_DIARIO_GLOBAL


@router.post("/chat", dependencies=[Depends(exigir_activo), Depends(verificar_origen)])
async def chat(datos: ChatRequest, request: Request, db: Session = Depends(get_db),
               conversacion_id: str = Depends(conversacion_del_token)):
    """Responde un mensaje del visitante en tiempo real (Server-Sent Events). Recibe el mensaje."""
    huella = _huella(request)
    conversacion = await run_in_threadpool(repo.obtener, db, conversacion_id)
    if conversacion is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "La conversación ya no existe. Vuelve a abrir el chat.")
    if not limitador.permitir(f"chat:{huella}", settings.ATENCION_MENSAJES_POR_MINUTO_IP, 60):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Vas muy rápido: espera un momento antes de seguir.")
    con_ia = await run_in_threadpool(_verificar_topes, db, conversacion, huella)
    if not con_ia:
        log.warning("Tope diario global de IA alcanzado: se responde con la base de conocimiento")

    cadena = request.app.state.cadena
    http_ia = request.app.state.http_ia
    http_core = request.app.state.http_core
    ip = ip_cliente(request)

    async def flujo():
        """Convierte los eventos del servicio en Server-Sent Events con su propia sesion de BD. Sin input."""
        sesion = SessionLocal()
        try:
            propia = sesion.get(type(conversacion), conversacion.id)
            async for evento in chat_service.conversar(sesion, propia, datos.mensaje, datos.origen, cadena, http_ia, con_ia,
                                                       http_core, ip):
                yield f"data: {json.dumps(evento, ensure_ascii=False)}\n\n"
        except Exception:
            # Un error a mitad de la respuesta no debe dejar el widget colgado ni mostrar detalles internos.
            referencia = secrets.token_hex(4).upper()
            log.exception("Error %s respondiendo en la conversación %s", referencia, conversacion.id[:8])
            evento = {"tipo": "error", "mensaje": f"Ocurrió un error. Código de referencia: {referencia}"}
            yield f"data: {json.dumps(evento, ensure_ascii=False)}\n\n"
        finally:
            sesion.close()

    return StreamingResponse(flujo(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
