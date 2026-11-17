# Acceso a las tablas de conversaciones y mensajes del modulo.
from datetime import datetime, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.fechas import ahora_utc
from app.models.conversacion import Conversacion, Mensaje


def crear(db: Session, conversacion_id: str, ip_huella: str, idioma: str, pagina: str) -> Conversacion:
    """Crea una conversacion nueva con el aviso de privacidad aceptado. Recibe id, huella de IP, idioma y pagina."""
    conversacion = Conversacion(id=conversacion_id, ip_huella=ip_huella, idioma=idioma, pagina=pagina)
    db.add(conversacion)
    db.commit()
    db.refresh(conversacion)
    return conversacion


def obtener(db: Session, conversacion_id: str) -> Conversacion | None:
    """Busca una conversacion por id. Recibe el id."""
    return db.get(Conversacion, conversacion_id)


def ultimos_mensajes(db: Session, conversacion_id: str, limite: int) -> list[Mensaje]:
    """Ultimos mensajes de la conversacion en orden cronologico. Recibe id y cuantos."""
    filas = db.execute(
        select(Mensaje).where(Mensaje.conversacion_id == conversacion_id).order_by(Mensaje.id.desc()).limit(limite)
    ).scalars().all()
    return list(reversed(filas))


def agregar_mensaje(db: Session, conversacion: Conversacion, rol: str, contenido: str, **extra) -> Mensaje:
    """Guarda un mensaje y actualiza la conversacion. Recibe conversacion, rol, contenido y campos extra."""
    mensaje = Mensaje(conversacion_id=conversacion.id, rol=rol, contenido=contenido, **extra)
    db.add(mensaje)
    conversacion.actualizada_en = ahora_utc()
    if rol == "usuario":
        conversacion.mensajes_usuario = (conversacion.mensajes_usuario or 0) + 1
    if extra.get("idioma"):
        conversacion.idioma = extra["idioma"]
    db.commit()
    db.refresh(mensaje)
    return mensaje


def contar_mensajes_usuario_desde(db: Session, desde: datetime, ip_huella: str | None = None) -> int:
    """Mensajes del visitante desde un momento, de una IP o de todas. Recibe el momento y la huella (opcional)."""
    consulta = select(func.count(Mensaje.id)).where(Mensaje.rol == "usuario", Mensaje.creado_en >= desde)
    if ip_huella:
        consulta = consulta.join(Conversacion, Conversacion.id == Mensaje.conversacion_id).where(
            Conversacion.ip_huella == ip_huella)
    return int(db.execute(consulta).scalar() or 0)


def purgar_antiguas(db: Session, dias: int) -> int:
    """Borra las conversaciones (y sus mensajes) sin actividad en los ultimos dias. Recibe los dias; devuelve cuantas."""
    limite = ahora_utc() - timedelta(days=dias)
    ids = db.execute(select(Conversacion.id).where(Conversacion.actualizada_en < limite)).scalars().all()
    if not ids:
        return 0
    # Primero lo que depende de la conversacion: SQLite (pruebas) no aplica ON DELETE CASCADE sin activarlo.
    from app.models.gestion import Accion, Derivacion

    for modelo in (Mensaje, Accion, Derivacion):
        db.execute(delete(modelo).where(modelo.conversacion_id.in_(ids)))
    db.execute(delete(Conversacion).where(Conversacion.id.in_(ids)))
    db.commit()
    return len(ids)
