# Propuestas de accion y su auditoria. Los cambios de estado se hacen con un UPDATE condicionado
# (WHERE estado = 'PENDIENTE' ...): si dos clics llegan a la vez, solo uno lo logra.
from datetime import datetime, timedelta

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.core.fechas import ahora_utc
from app.models import propuesta_accion as M
from app.models.propuesta_accion import AuditoriaAccion, PropuestaAccion


def auditar(db: Session, usuario: dict, evento: str, propuesta: PropuestaAccion | None = None,
            accion: str | None = None, detalle: str | None = None) -> None:
    """Guarda un paso de una accion con el usuario que lo hizo. Recibe db, usuario, evento, propuesta y detalle."""
    db.add(AuditoriaAccion(
        propuesta_id=propuesta.id if propuesta else None,
        evento=evento,
        accion=(propuesta.accion if propuesta else accion),
        usuario_id=usuario["id"],
        usuario_correo=usuario.get("correo", ""),
        rol=usuario.get("rol", ""),
        detalle=(detalle or "")[:1000] or None,
    ))
    db.commit()


def crear(db: Session, usuario: dict, sesion: str, conversacion_id: str | None, accion: str,
          objetivo: dict, titulo: str, detalle: str, vence_seg: int) -> PropuestaAccion:
    """Guarda una propuesta PENDIENTE y la audita. Recibe db, usuario, sesion, conversacion y datos de la accion."""
    ahora = ahora_utc()
    propuesta = PropuestaAccion(
        usuario_id=usuario["id"], usuario_correo=usuario.get("correo", ""), rol=usuario["rol"], sesion=sesion,
        conversacion_id=conversacion_id, accion=accion, objetivo=objetivo, titulo=titulo[:120], detalle=detalle,
        estado=M.PENDIENTE, creada_en=ahora, vence_en=ahora + timedelta(seconds=vence_seg),
    )
    db.add(propuesta)
    db.commit()
    db.refresh(propuesta)
    auditar(db, usuario, "propuesta", propuesta, detalle=titulo)
    return propuesta


def obtener(db: Session, propuesta_id: str) -> PropuestaAccion | None:
    """Devuelve una propuesta por su id. Recibe db e id."""
    return db.get(PropuestaAccion, propuesta_id)


def _cambiar(db: Session, propuesta_id: str, desde: str, hacia: str, *, vigente_en: datetime | None = None,
             resultado: str | None = None) -> bool:
    """Cambia el estado solo si sigue en 'desde' (y vigente, si se pide). Devuelve si lo logro. Recibe db, id y estados."""
    condicion = [PropuestaAccion.id == propuesta_id, PropuestaAccion.estado == desde]
    if vigente_en is not None:
        condicion.append(PropuestaAccion.vence_en > vigente_en)
    valores = {"estado": hacia}
    if hacia != M.EN_CURSO:
        valores["resuelta_en"] = ahora_utc()
    if resultado is not None:
        valores["resultado"] = resultado[:1000]
    filas = db.execute(update(PropuestaAccion).where(*condicion).values(**valores)).rowcount
    db.commit()
    return filas == 1


def tomar_para_ejecutar(db: Session, propuesta_id: str) -> bool:
    """PENDIENTE y vigente -> EN_CURSO, de forma atomica (una propuesta = una ejecucion). Recibe db e id."""
    return _cambiar(db, propuesta_id, M.PENDIENTE, M.EN_CURSO, vigente_en=ahora_utc())


def cancelar(db: Session, propuesta_id: str) -> bool:
    """PENDIENTE y vigente -> CANCELADA. Recibe db e id."""
    return _cambiar(db, propuesta_id, M.PENDIENTE, M.CANCELADA, vigente_en=ahora_utc())


def terminar(db: Session, propuesta_id: str, ok: bool, resultado: str) -> None:
    """EN_CURSO -> EJECUTADA o ERROR con el mensaje del nucleo. Recibe db, id, si salio bien y el mensaje."""
    _cambiar(db, propuesta_id, M.EN_CURSO, M.EJECUTADA if ok else M.ERROR, resultado=resultado)


def vencer_si_corresponde(db: Session, propuesta: PropuestaAccion, usuario: dict) -> bool:
    """Si la propuesta PENDIENTE ya vencio, la marca VENCIDA y lo audita. Devuelve si vencio. Recibe db, propuesta y usuario."""
    if propuesta.estado != M.PENDIENTE or propuesta.vence_en > ahora_utc():
        return False
    if _cambiar(db, propuesta.id, M.PENDIENTE, M.VENCIDA, resultado="Venció sin confirmar"):
        auditar(db, usuario, "vencida", propuesta)
    db.refresh(propuesta)
    return True


def cerrar_pendientes(db: Session, usuario: dict, excepto_conversacion: str | None = None,
                      solo_conversacion: str | None = None) -> int:
    """Cierra las propuestas PENDIENTE del usuario: las vencidas pasan a VENCIDA y el resto a INVALIDADA
    (se cambio o se borro la conversacion). Recibe db, usuario y que conversacion conservar o cerrar."""
    consulta = db.query(PropuestaAccion).filter(
        PropuestaAccion.usuario_id == usuario["id"], PropuestaAccion.estado == M.PENDIENTE
    )
    if solo_conversacion is not None:
        consulta = consulta.filter(PropuestaAccion.conversacion_id == solo_conversacion)
    ahora = ahora_utc()
    cerradas = 0
    for propuesta in consulta.all():
        vencida = propuesta.vence_en <= ahora
        if vencida:
            if _cambiar(db, propuesta.id, M.PENDIENTE, M.VENCIDA, resultado="Venció sin confirmar"):
                auditar(db, usuario, "vencida", propuesta)
                cerradas += 1
        elif propuesta.conversacion_id != excepto_conversacion or solo_conversacion is not None:
            if _cambiar(db, propuesta.id, M.PENDIENTE, M.INVALIDADA, resultado="Se cambió de conversación"):
                auditar(db, usuario, "invalidada", propuesta, detalle="Se cambió o se borró la conversación")
                cerradas += 1
    return cerradas


def estados(db: Session, ids: list[str], usuario_id: int) -> dict[str, PropuestaAccion]:
    """Propuestas propias por id (para mostrar su estado actual en el historial). Recibe db, ids y usuario_id."""
    if not ids:
        return {}
    filas = db.query(PropuestaAccion).filter(PropuestaAccion.id.in_(ids), PropuestaAccion.usuario_id == usuario_id).all()
    return {p.id: p for p in filas}


def de_conversacion(db: Session, conversacion_id: str, usuario_id: int, limite: int = 5) -> list[PropuestaAccion]:
    """Ultimas propuestas de una conversacion, de la mas antigua a la mas nueva. Recibe db, conversacion, usuario y limite."""
    filas = (
        db.query(PropuestaAccion)
        .filter(PropuestaAccion.conversacion_id == conversacion_id, PropuestaAccion.usuario_id == usuario_id)
        .order_by(PropuestaAccion.creada_en.desc())
        .limit(limite)
        .all()
    )
    return list(reversed(filas))
