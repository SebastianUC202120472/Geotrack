"""Resuelve a quien va cada aviso desde la configuracion y los datos del sistema."""
from app.core.config import settings
from app.models.notificacion_contacto import NotificacionContacto


def email_admin() -> str:
    """Correo del administrador; destino de los avisos internos."""
    return settings.ADMIN_EMAIL


def email_almacen() -> str:
    """Correo del almacen; cae al del administrador si no hay uno propio."""
    return (settings.NOTIFICACIONES_ALMACEN_EMAIL or "").strip() or settings.ADMIN_EMAIL


def telegram_admin() -> str:
    """Chat de Telegram del administrador para los avisos urgentes."""
    return (settings.NOTIFICACIONES_ADMIN_TELEGRAM_CHAT_ID or "").strip()


def telegram_contacto(db, entidad_tipo: str, entidad_id: int | None) -> tuple[str, str | None]:
    """Busca el chat_id activo de una entidad; devuelve valor y nombre."""
    if db is None or entidad_id is None:
        return "", None

    if entidad_tipo == "mecanico":
        from app.models.notificacion_mecanico import NotificacionMecanico
        mec = (
            db.query(NotificacionMecanico)
            .filter(
                NotificacionMecanico.id == entidad_id,
                NotificacionMecanico.activo.is_(True),
            )
            .first()
        )
        if mec and mec.telegram_chat_id:
            return (mec.telegram_chat_id.strip(), mec.nombre)

    contacto = (
        db.query(NotificacionContacto)
        .filter(
            NotificacionContacto.entidad_tipo == entidad_tipo,
            NotificacionContacto.entidad_id == entidad_id,
            NotificacionContacto.canal == "telegram",
            NotificacionContacto.activo.is_(True),
        )
        .first()
    )
    if contacto is None:
        return "", None
    return (contacto.valor or "").strip(), contacto.nombre


def email_cliente(cliente) -> str:
    """Correo del cliente corporativo (el del portal); vacio si no tiene."""
    return (getattr(cliente, "correo_portal", None) or "").strip()


def enlace_portal() -> str:
    """URL publica del portal de rastreo para los mensajes al destinatario."""
    return (settings.NOTIFICACIONES_URL_PORTAL or "").strip() or "https://sava.pe/portal"
