# Acceso a datos del centro de notificaciones: bitacora de envios, directorio de mecanicos,
# contactos vinculados, bajas (STOP) y plantillas. Solo consultas: la logica vive en los servicios.
from typing import Optional

from sqlalchemy.orm import Session

from app.models.incidencia import Incidencia
from app.models.notificacion_contacto import NotificacionContacto
from app.models.notificacion_envio import NotificacionEnvio
from app.models.notificacion_mecanico import NotificacionMecanico
from app.models.notificacion_plantilla import NotificacionBaja, NotificacionPlantilla


# --- Bitacora de envios ---

def listar_envios(db: Session, estado: Optional[str], canal: Optional[str], evento: Optional[str],
                  limite: int, offset: int) -> tuple[int, list[NotificacionEnvio]]:
    """Total y pagina de envios con filtros opcionales. Recibe filtros, limite y offset."""
    q = db.query(NotificacionEnvio)
    if estado:
        q = q.filter(NotificacionEnvio.estado == estado.upper())
    if canal:
        q = q.filter(NotificacionEnvio.canal == canal.lower())
    if evento:
        q = q.filter(NotificacionEnvio.evento == evento.upper())
    total = q.count()
    return total, q.order_by(NotificacionEnvio.id.desc()).offset(offset).limit(limite).all()


def obtener_envio(db: Session, envio_id: int) -> Optional[NotificacionEnvio]:
    """Un envio por id. Recibe el id."""
    return db.query(NotificacionEnvio).filter(NotificacionEnvio.id == envio_id).first()


def existe_clave(db: Session, clave: str) -> bool:
    """True si ya hay un envio con esa clave de idempotencia. Recibe la clave."""
    return db.query(NotificacionEnvio.id).filter(NotificacionEnvio.clave_idempotencia == clave).first() is not None


def claves_con_prefijo(db: Session, prefijo: str) -> list[str]:
    """Claves de idempotencia que empiezan con el prefijo. Recibe el prefijo."""
    filas = db.query(NotificacionEnvio.clave_idempotencia).filter(
        NotificacionEnvio.clave_idempotencia.like(f"{prefijo}%")).all()
    return [c for (c,) in filas]


# --- Directorio de mecanicos ---

def listar_mecanicos(db: Session) -> list[NotificacionMecanico]:
    """Todos los mecanicos por nombre. Sin input extra."""
    return db.query(NotificacionMecanico).order_by(NotificacionMecanico.nombre.asc()).all()


def obtener_mecanico(db: Session, mecanico_id: int) -> Optional[NotificacionMecanico]:
    """Un mecanico por id. Recibe el id."""
    return db.query(NotificacionMecanico).filter(NotificacionMecanico.id == mecanico_id).first()


def obtener_mecanico_por_telefono(db: Session, telefono: str) -> Optional[NotificacionMecanico]:
    """Un mecanico por su telefono tal como se guardo. Recibe el telefono."""
    return db.query(NotificacionMecanico).filter(NotificacionMecanico.telefono_whatsapp == telefono).first()


def obtener_mecanico_por_chat(db: Session, chat_id: str) -> Optional[NotificacionMecanico]:
    """Un mecanico por su chat de Telegram. Recibe el chat_id."""
    return db.query(NotificacionMecanico).filter(NotificacionMecanico.telegram_chat_id == chat_id).first()


def mecanicos_verificados(db: Session, tipo: Optional[str] = None) -> list[NotificacionMecanico]:
    """Mecanicos activos con numero verificado, opcionalmente de un tipo de servicio. Recibe el tipo."""
    q = db.query(NotificacionMecanico).filter(
        NotificacionMecanico.activo.is_(True), NotificacionMecanico.telefono_verificado.is_(True))
    if tipo:
        q = q.filter(NotificacionMecanico.tipo_servicio == tipo)
    return q.all()


def guardar(db: Session, objeto) -> None:
    """Agrega un objeto nuevo a la sesion (sin confirmar). Recibe el objeto."""
    db.add(objeto)


def eliminar(db: Session, objeto) -> None:
    """Borra un objeto (sin confirmar). Recibe el objeto."""
    db.delete(objeto)


# --- Contactos vinculados (Telegram) ---

def obtener_contacto(db: Session, entidad_tipo: str, entidad_id: int, canal: str) -> Optional[NotificacionContacto]:
    """El contacto de una entidad en un canal. Recibe tipo, id y canal."""
    return db.query(NotificacionContacto).filter(
        NotificacionContacto.entidad_tipo == entidad_tipo,
        NotificacionContacto.entidad_id == entidad_id,
        NotificacionContacto.canal == canal,
    ).first()


def guardar_contacto(db: Session, entidad_tipo: str, entidad_id: int, canal: str, valor: str,
                     nombre: Optional[str]) -> NotificacionContacto:
    """Crea o reactiva el contacto de una entidad en un canal (sin confirmar). Recibe sus datos."""
    contacto = obtener_contacto(db, entidad_tipo, entidad_id, canal)
    if contacto is None:
        contacto = NotificacionContacto(entidad_tipo=entidad_tipo, entidad_id=entidad_id, canal=canal,
                                        valor=valor, nombre=nombre, activo=True)
        db.add(contacto)
    else:
        contacto.valor, contacto.activo = valor, True
        contacto.nombre = nombre or contacto.nombre
    return contacto


def contactos_activos(db: Session, entidad_tipo: str, canal: str) -> list[NotificacionContacto]:
    """Contactos activos de un tipo de entidad en un canal. Recibe tipo y canal."""
    return db.query(NotificacionContacto).filter(
        NotificacionContacto.entidad_tipo == entidad_tipo,
        NotificacionContacto.canal == canal,
        NotificacionContacto.activo.is_(True),
    ).all()


def desactivar_contactos_por_valor(db: Session, canal: str, valor: str) -> int:
    """Desactiva los contactos de ese chat o telefono. Recibe canal y valor. Devuelve cuantos."""
    contactos = db.query(NotificacionContacto).filter(
        NotificacionContacto.canal == canal, NotificacionContacto.valor == valor).all()
    for c in contactos:
        c.activo = False
    return len(contactos)


# --- Bajas (Ley 29733) ---

def registrar_baja(db: Session, canal: str, valor: str, motivo: str = "STOP") -> None:
    """Registra la baja de un chat o telefono si aun no estaba. Recibe canal, valor y motivo."""
    if not esta_de_baja(db, canal, valor):
        db.add(NotificacionBaja(canal=canal, valor=valor, motivo=motivo))


def quitar_baja(db: Session, canal: str, valor: str) -> None:
    """Borra la baja cuando la persona vuelve a suscribirse a proposito. Recibe canal y valor."""
    db.query(NotificacionBaja).filter(NotificacionBaja.canal == canal, NotificacionBaja.valor == valor).delete()


def esta_de_baja(db: Session, canal: str, valor: str) -> bool:
    """True si ese chat o telefono pidio no recibir mensajes. Recibe canal y valor."""
    return db.query(NotificacionBaja.id).filter(
        NotificacionBaja.canal == canal, NotificacionBaja.valor == valor).first() is not None


# --- Lecturas del nucleo que necesita el auxilio ---

def obtener_incidencia_por_codigo(db: Session, codigo: str) -> Optional[Incidencia]:
    """Una incidencia por su codigo legible (IN-001). Recibe el codigo."""
    return db.query(Incidencia).filter(Incidencia.codigo == codigo).first()


# --- Plantillas ---

def listar_plantillas(db: Session) -> list[NotificacionPlantilla]:
    """Todas las plantillas por evento. Sin input extra."""
    return db.query(NotificacionPlantilla).order_by(NotificacionPlantilla.evento, NotificacionPlantilla.canal).all()


def obtener_plantilla(db: Session, plantilla_id: int) -> Optional[NotificacionPlantilla]:
    """Una plantilla por id. Recibe el id."""
    return db.query(NotificacionPlantilla).filter(NotificacionPlantilla.id == plantilla_id).first()


def obtener_plantilla_evento(db: Session, evento: str, canal: str) -> Optional[NotificacionPlantilla]:
    """La plantilla de un evento en un canal, si el administrador la creo. Recibe evento y canal."""
    return db.query(NotificacionPlantilla).filter(
        NotificacionPlantilla.evento == evento, NotificacionPlantilla.canal == canal).first()
