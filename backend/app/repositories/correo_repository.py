# app/repositories/correo_repository.py
# Única capa que consulta/escribe en las tablas de conversaciones y mensajes. La USA.
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.correo import Conversacion, MensajeCorreo, MensajeAdjunto


def listar_conversaciones(db: Session) -> List[Conversacion]:
    """Conversaciones ordenadas por actividad más reciente."""
    return (
        db.query(Conversacion)
        .order_by(Conversacion.ultimo_mensaje_en.desc())
        .all()
    )


def obtener_conversacion(db: Session, conversacion_id: int) -> Optional[Conversacion]:
    return db.query(Conversacion).filter(Conversacion.id == conversacion_id).first()


def buscar_o_crear_conversacion(
    db: Session, contraparte_email: str, asunto: str, asunto_normalizado: str, nombre: Optional[str] = None
) -> Conversacion:
    """Agrupa por contraparte + asunto normalizado (sin 'Re:'); crea el hilo si no existe."""
    conv = (
        db.query(Conversacion)
        .filter(
            Conversacion.contraparte_email == contraparte_email,
            Conversacion.asunto_normalizado == asunto_normalizado,
        )
        .first()
    )
    if not conv:
        conv = Conversacion(
            contraparte_email=contraparte_email,
            contraparte_nombre=nombre,
            asunto=asunto or "(sin asunto)",
            asunto_normalizado=asunto_normalizado,
        )
        db.add(conv)
        db.flush()
    return conv


def existe_mensaje(db: Session, message_id: str) -> bool:
    """Evita importar dos veces el mismo correo (por su Message-ID)."""
    if not message_id:
        return False
    return (
        db.query(MensajeCorreo.id)
        .filter(MensajeCorreo.message_id == message_id)
        .first()
        is not None
    )


def agregar_mensaje(db: Session, conversacion: Conversacion, **datos) -> MensajeCorreo:
    mensaje = MensajeCorreo(conversacion_id=conversacion.id, **datos)
    db.add(mensaje)
    db.flush()  # asigna el id para poder colgarle adjuntos
    # La actividad del hilo se mueve a la fecha del mensaje.
    conversacion.ultimo_mensaje_en = datos.get("fecha") or datetime.utcnow()
    return mensaje


def agregar_adjunto(db: Session, mensaje: MensajeCorreo, nombre_archivo: str, content_type: str, contenido: bytes) -> MensajeAdjunto:
    adjunto = MensajeAdjunto(
        mensaje_id=mensaje.id,
        nombre_archivo=nombre_archivo,
        content_type=content_type,
        tamano=len(contenido or b""),
        contenido=contenido,
    )
    db.add(adjunto)
    return adjunto


def obtener_adjunto(db: Session, adjunto_id: int) -> Optional[MensajeAdjunto]:
    return db.query(MensajeAdjunto).filter(MensajeAdjunto.id == adjunto_id).first()


def marcar_leida(db: Session, conversacion: Conversacion) -> None:
    """Al abrir el hilo: marca los mensajes como leídos y reinicia el contador."""
    conversacion.no_leidos = 0
    for m in conversacion.mensajes:
        if not m.leido:
            m.leido = True
    db.commit()


def cambiar_estado(db: Session, conversacion: Conversacion, estado: str) -> Conversacion:
    conversacion.estado = estado
    db.commit()
    db.refresh(conversacion)
    return conversacion
