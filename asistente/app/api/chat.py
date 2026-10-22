import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.api.deps import obtener_usuario
from app.core.config import settings
from app.core.fechas import ahora_local
from app.core.limites import limitador
from app.db.database import SessionLocal, get_db
from app.ia import transcripcion
from app.ia.transcripcion import ErrorAudio, ErrorTranscripcion
from app.repositories import auditoria_repository
from app.schemas.chat import ChatRequest, EstadoResponse, TranscripcionResponse
from app.services import chat_service

router = APIRouter()


def _inicio_del_dia_utc() -> datetime:
    """Medianoche de hoy (hora de Lima) expresada en UTC sin zona. Sin input."""
    medianoche = ahora_local().replace(hour=0, minute=0, second=0, microsecond=0)
    return medianoche.astimezone(timezone.utc).replace(tzinfo=None)


@router.get("/estado", response_model=EstadoResponse)
def estado(request: Request):
    """Dice si el asistente esta activo y si transcribe voz en el servidor. Sin input."""
    cadena = getattr(request.app.state, "cadena", None)
    return EstadoResponse(
        activo=bool(settings.ASISTENTE_ENABLED and cadena and cadena.proveedores),
        voz_servidor=transcripcion.voz_en_servidor_disponible(),
        max_caracteres=settings.ASISTENTE_MAX_CARACTERES,
        max_seg_voz=settings.ASISTENTE_VOZ_MAX_SEG,
    )


def _verificar_tope_diario(db: Session, usuario: dict, origen: str) -> None:
    """Corta con 429 si el usuario llego al tope de preguntas del dia. Recibe db, usuario y origen."""
    usados = auditoria_repository.contar_desde(db, usuario["id"], _inicio_del_dia_utc())
    if usados >= settings.ASISTENTE_MENSAJES_POR_DIA:
        auditoria_repository.registrar(
            db, usuario_id=usuario["id"], usuario_correo=usuario["correo"], rol=usuario["rol"],
            origen=origen, pregunta="", resultado="limite",
        )
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Llegaste al tope de preguntas de hoy. Vuelve a intentarlo mañana.")


@router.post("/chat")
async def chat(datos: ChatRequest, request: Request, db: Session = Depends(get_db), usuario: dict = Depends(obtener_usuario)):
    """Responde una pregunta en tiempo real (Server-Sent Events). Recibe el mensaje y la conversacion."""
    if not limitador.permitir(f"chat:{usuario['id']}", settings.ASISTENTE_MENSAJES_POR_MINUTO, 60):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Vas muy rápido: espera un minuto antes de seguir preguntando.")
    await run_in_threadpool(_verificar_tope_diario, db, usuario, datos.origen)

    cadena = request.app.state.cadena
    if not cadena.proveedores:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "No hay proveedores de IA configurados")

    async def flujo():
        """Convierte los eventos del servicio en Server-Sent Events con su propia sesion de BD. Sin input."""
        sesion = SessionLocal()
        try:
            async for evento in chat_service.conversar(
                sesion, usuario, usuario["token"], datos.mensaje, datos.conversacion_id, datos.origen,
                cadena, request.app.state.http_ia, getattr(request.app.state, "http_core", None),
            ):
                yield f"data: {json.dumps(evento, ensure_ascii=False, default=str)}\n\n"
        finally:
            sesion.close()

    return StreamingResponse(
        flujo(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/voz", response_model=TranscripcionResponse)
async def voz(request: Request, audio: UploadFile = File(...), usuario: dict = Depends(obtener_usuario)):
    """Transcribe un mensaje de voz y descarta el audio. Recibe el archivo de audio."""
    if not limitador.permitir(f"voz:{usuario['id']}", settings.ASISTENTE_AUDIOS_POR_MINUTO, 60):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Demasiados audios seguidos: espera un minuto.")
    maximo = settings.ASISTENTE_VOZ_MAX_KB * 1024
    contenido = await audio.read(maximo + 1)
    await audio.close()
    try:
        transcripcion.validar_audio(contenido)
        texto = await transcripcion.transcribir(contenido, getattr(request.app.state, "http_ia", None))
    except ErrorAudio as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    except ErrorTranscripcion as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc))
    finally:
        del contenido   # el audio no se guarda en ningun lado
    texto = texto[: settings.ASISTENTE_MAX_CARACTERES]
    if not texto:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No se entendió el audio. Intenta de nuevo.")
    return TranscripcionResponse(texto=texto)
