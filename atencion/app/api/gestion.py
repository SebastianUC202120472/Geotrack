# Endpoints publicos que el widget llama SIN pasar por el modelo de IA:
#   - verificar: formulario de los ultimos 4 digitos del DNI (van directo al portal, no se guardan),
#   - acciones: el clic en Confirmar o Cancelar de una tarjeta (el modelo solo propone),
#   - derivaciones: boton "Hablar con una persona",
#   - voz: transcripcion de un mensaje de voz (el audio se descarta).
# Todos exigen el modulo activo, el origen del sitio y el token de SU conversacion.
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.api.deps import conversacion_del_token, exigir_activo, verificar_origen
from app.core import tokens
from app.core.config import settings
from app.core.limites import limitador
from app.core.red import huella_ip, ip_cliente
from app.core.registro import log
from app.db.database import get_db
from app.herramientas import funciones
from app.herramientas.cliente_portal import (
    Bloqueado, ClientePortal, DatosRetirados, ErrorPortal, NoEncontrado, Rechazado, VerificacionFallida, codigo_valido,
)
from app.ia import transcripcion
from app.ia.transcripcion import ErrorAudio, ErrorTranscripcion
from app.repositories import conversacion_repository as repo
from app.schemas.chat import (
    DerivacionRequest, DerivacionResponse, ResultadoAccion, TranscripcionResponse, VerificarRequest, VerificarResponse,
)
from app.services import acciones_service
from app.services.privacidad import enmascarar_texto
from app.services.sesion import sesiones

router = APIRouter(dependencies=[Depends(exigir_activo), Depends(verificar_origen)])

MENSAJES_VERIFICADO = {
    "es": "Listo, ya verifiqué mi pedido {codigo}. ¿Cómo va?",
    "en": "Done, I verified my order {codigo}. How is it going?",
}
DERIVADA = {
    "es": "Listo: tu conversación quedó con el equipo de SAVA y una persona la revisará{extra}.",
    "en": "Done: your conversation is now with the SAVA team and a person will review it{extra}.",
}
DERIVADA_CONTACTO = {"es": " y te contactará por el medio que indicaste", "en": " and contact you as you indicated"}


def _conversacion(db: Session, conversacion_id: str):
    """Conversacion del token o 401 si ya no existe. Recibe db e id."""
    conversacion = repo.obtener(db, conversacion_id)
    if conversacion is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "La conversación ya no existe. Vuelve a abrir el chat.")
    return conversacion


def _portal(request: Request) -> ClientePortal:
    """Cliente del portal en nombre del visitante (con su IP real). Recibe la peticion."""
    return ClientePortal(request.app.state.http_core, ip_cliente(request))


@router.post("/verificar", response_model=VerificarResponse)
async def verificar(datos: VerificarRequest, request: Request, db: Session = Depends(get_db),
                    conversacion_id: str = Depends(conversacion_del_token)):
    """Verifica un pedido con los ultimos 4 digitos del DNI y recuerda el token de portal en el servidor.
    Recibe codigo y digitos. Los digitos no se registran en ningun lado."""
    conversacion = await run_in_threadpool(_conversacion, db, conversacion_id)
    codigo = codigo_valido(datos.codigo)
    if not codigo:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El código del pedido no es válido")
    estado = sesiones.de(conversacion.id)
    if estado.verificaciones >= settings.ATENCION_VERIFICACIONES_POR_CONVERSACION:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Demasiados intentos de verificación en esta conversación.")
    estado.verificaciones += 1
    try:
        respuesta = await _portal(request).verificar(codigo, datos.digitos)
    except VerificacionFallida as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, {"mensaje": "Los dígitos no coinciden.",
                                                           "intentos_restantes": exc.restantes})
    except Bloqueado as exc:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, {"mensaje": "Demasiados intentos. Espera un momento.",
                                                                "bloqueado_segundos": exc.segundos})
    except NoEncontrado:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No hay un pedido con ese código.")
    except DatosRetirados:
        raise HTTPException(status.HTTP_410_GONE, "Este pedido ya no está disponible para consulta.")
    except (Rechazado, ErrorPortal):
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "El rastreo no responde ahora. Intenta en unos minutos.")
    token = respuesta.get("token")
    if not token:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "El rastreo no responde ahora. Intenta en unos minutos.")
    estado.guardar_token(codigo, token)
    log.info("Pedido verificado en la conversación %s", conversacion.id[:8])
    idioma = conversacion.idioma if conversacion.idioma in MENSAJES_VERIFICADO else "es"
    return VerificarResponse(ok=True, codigo=codigo, mensaje_sugerido=MENSAJES_VERIFICADO[idioma].format(codigo=codigo))


@router.post("/acciones/{ident}/confirmar", response_model=ResultadoAccion)
async def confirmar(ident: str, request: Request, db: Session = Depends(get_db),
                    conversacion_id: str = Depends(conversacion_del_token)):
    """Ejecuta la propuesta que el visitante confirmo con un clic. Recibe el id de la propuesta."""
    if not ident.isalnum() or len(ident) != 32:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "La acción no existe")
    conversacion = await run_in_threadpool(_conversacion, db, conversacion_id)
    try:
        resultado = await acciones_service.confirmar(db, conversacion, sesiones.de(conversacion.id), ident, _portal(request))
    except acciones_service.AccionNoValida as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
    return ResultadoAccion(**resultado)


@router.post("/acciones/{ident}/cancelar", response_model=ResultadoAccion)
def cancelar(ident: str, db: Session = Depends(get_db), conversacion_id: str = Depends(conversacion_del_token)):
    """Cancela una propuesta pendiente sin hacer cambios. Recibe el id de la propuesta."""
    conversacion = _conversacion(db, conversacion_id)
    try:
        return ResultadoAccion(**acciones_service.cancelar(db, conversacion, sesiones.de(conversacion.id), ident))
    except acciones_service.AccionNoValida as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))


@router.post("/derivaciones", response_model=DerivacionResponse, status_code=201)
async def derivar(datos: DerivacionRequest, request: Request, db: Session = Depends(get_db),
                  conversacion_id: str = Depends(conversacion_del_token)):
    """Boton "Hablar con una persona": deja la conversacion en la bandeja del equipo. Recibe motivo y contacto."""
    conversacion = await run_in_threadpool(_conversacion, db, conversacion_id)
    estado = sesiones.de(conversacion.id)
    # El contacto llega del formulario del widget (no del modelo): se guarda tal cual para devolver la llamada.
    contacto = datos.contacto
    motivo = enmascarar_texto(datos.motivo or "El visitante pidió hablar con una persona")
    ctx = funciones.Contexto(db, conversacion, estado, _portal(request), conversacion.idioma)
    resultado, _ = await funciones.derivar_a_persona(ctx, motivo, None, origen="visitante", contacto_real=contacto)
    idioma = conversacion.idioma if conversacion.idioma in DERIVADA else "es"
    extra = DERIVADA_CONTACTO[idioma] if contacto else ""
    return DerivacionResponse(ok=bool(resultado.get("derivada")), mensaje=DERIVADA[idioma].format(extra=extra))


@router.post("/voz", response_model=TranscripcionResponse)
async def voz(request: Request, audio: UploadFile = File(...), db: Session = Depends(get_db),
              conversacion_id: str = Depends(conversacion_del_token)):
    """Transcribe un mensaje de voz y descarta el audio. Recibe el archivo; el widget luego envia el texto al chat."""
    conversacion = await run_in_threadpool(_conversacion, db, conversacion_id)
    estado = sesiones.de(conversacion.id)
    huella = huella_ip(ip_cliente(request), tokens.SECRETO)
    if not limitador.permitir(f"voz:{huella}", settings.ATENCION_AUDIOS_POR_MINUTO_IP, 60):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Demasiados audios seguidos: espera un minuto.")
    if estado.audios >= settings.ATENCION_AUDIOS_POR_CONVERSACION:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Esta conversación llegó a su límite de audios.")
    estado.audios += 1
    maximo = settings.ATENCION_VOZ_MAX_KB * 1024
    contenido = await audio.read(maximo + 1)
    await audio.close()
    try:
        texto, idioma = await transcripcion.transcribir(contenido, request.app.state.http_ia)
    except ErrorAudio as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    except ErrorTranscripcion as exc:
        log.warning("Transcripción fallida: %s", exc)
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "No se pudo transcribir el audio. Escribe tu mensaje.")
    finally:
        del contenido   # el audio no se guarda en ningun lado
    texto = texto[: settings.ATENCION_MAX_CARACTERES]
    if not texto:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No se entendió el audio. Intenta de nuevo.")
    return TranscripcionResponse(texto=texto, idioma=idioma)
