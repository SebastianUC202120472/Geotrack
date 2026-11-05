from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import socket

from app.models.notificacion_envio import NotificacionEnvio

_DURACION_CONCESION = timedelta(minutes=5)
_WORKER_ID = socket.gethostname()[:80]
MAX_INTENTOS = 3
_BACKOFF = (timedelta(minutes=1), timedelta(minutes=5), timedelta(minutes=15))


def crear_si_no_existe(db: Session, mensaje) -> bool:
    """Inserta la fila si su clave unica no existe; True si la creo, False si ya estaba.
    Recibe sesion de BD y un mensaje canónico del modulo de notificaciones."""
    fila = NotificacionEnvio(
        notificacion_id=mensaje.notificacion_id,
        evento=mensaje.evento,
        canal=mensaje.canal.value,
        destinatario_tipo=mensaje.destinatario.tipo,
        destinatario_valor=mensaje.destinatario.valor,
        destinatario_nombre=mensaje.destinatario.nombre,
        asunto=mensaje.asunto,
        cuerpo=mensaje.cuerpo,
        prioridad=mensaje.prioridad.value,
        clave_idempotencia=mensaje.clave_idempotencia,
    )
    try:
        # SAVEPOINT: si choca con otra fila, se deshace solo este insert y la transaccion sigue viva.
        with db.begin_nested():
            db.add(fila)
            db.flush()
        db.flush()
        return True
    except IntegrityError:
        return False


def listar_pendientes(db: Session, limite: int = 100, solo_urgentes: bool = False) -> list[NotificacionEnvio]:
    """Reclama pendientes con bloqueo temporal; devuelve las filas reclamadas.
    Si solo_urgentes es True (horario silencioso), solo toma prioridad 'urgente'."""
    ahora = datetime.utcnow()
    query = (
        db.query(NotificacionEnvio)
        .filter(NotificacionEnvio.estado == "PENDIENTE")
        .filter((NotificacionEnvio.proximo_intento_en == None) | (NotificacionEnvio.proximo_intento_en <= ahora))  # noqa: E711
        .filter((NotificacionEnvio.bloqueado_hasta == None) | (NotificacionEnvio.bloqueado_hasta <= ahora))  # noqa: E711
    )
    if solo_urgentes:
        query = query.filter(NotificacionEnvio.prioridad == "urgente")

    filas = (
        query
        .order_by(NotificacionEnvio.creado_en)
        .limit(limite)
        .with_for_update(skip_locked=True)
        .all()
    )
    for fila in filas:
        fila.bloqueado_hasta = ahora + _DURACION_CONCESION
        fila.worker_id = _WORKER_ID
    db.commit()
    return filas


def marcar_enviado(db: Session, fila: NotificacionEnvio) -> None:
    """Pasa la fila a ENVIADO con su fecha y limpia la concesion temporal."""
    from datetime import datetime
    fila.estado = "ENVIADO"
    fila.enviado_en = datetime.utcnow()
    fila.intentos = (fila.intentos or 0) + 1
    fila.bloqueado_hasta = None
    fila.worker_id = None


def marcar_fallido(db: Session, fila: NotificacionEnvio, detalle: str | None, reintentable: bool = False) -> None:
    """Registra un fallo y reprograma errores temporales hasta el limite configurado."""
    fila.estado = "FALLIDO"
    fila.intentos = (fila.intentos or 0) + 1
    texto = (detalle or "")[:220]
    fila.bloqueado_hasta = None
    fila.worker_id = None
    fila.proximo_intento_en = None
    if reintentable and fila.intentos < MAX_INTENTOS:
        fila.estado = "PENDIENTE"
        fila.proximo_intento_en = datetime.utcnow() + _BACKOFF[fila.intentos - 1]
        fila.detalle = f"Reintento {fila.intentos}/{MAX_INTENTOS} programado: {texto}"[:255]
    else:
        fila.detalle = texto
