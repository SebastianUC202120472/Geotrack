"""Adaptadores polimórficos de entrega: SMTP, Telegram Bot API y WhatsApp Cloud API."""
import json
import smtplib
import ssl
from email.message import EmailMessage
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import settings
from app.services.notificaciones_automaticas.plantillas_email import renderizar_email


def es_error_transitorio(exc: Exception) -> bool:
    """Indica si el proveedor puede recuperarse con otro intento."""
    if isinstance(exc, (smtplib.SMTPAuthenticationError, smtplib.SMTPRecipientsRefused)):
        return False
    if isinstance(exc, (smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected, TimeoutError, OSError)):
        return True
    if isinstance(exc, smtplib.SMTPDataError):
        return 400 <= int(exc.smtp_code) < 500
    if isinstance(exc, HTTPError):
        return exc.code == 429 or exc.code >= 500
    if isinstance(exc, URLError):
        return True
    return False


def enviar(fila) -> None:
    """Entrega una fila de la cola o lanza una excepción con el motivo."""
    canal = (fila.canal or "").lower()
    if canal == "correo":
        _enviar_correo(fila)
    elif canal == "telegram":
        _enviar_telegram(fila)
    elif canal == "whatsapp":
        _enviar_whatsapp(fila)
    else:
        raise ValueError(f"Canal no soportado: {fila.canal}")


def _enviar_correo(fila) -> None:
    if not settings.MAIL_ENABLED:
        raise RuntimeError("El correo está desactivado: MAIL_ENABLED=false")
    if not settings.MAIL_ADDRESS or not settings.MAIL_PASSWORD:
        raise RuntimeError("SMTP no está configurado: faltan MAIL_ADDRESS o MAIL_PASSWORD")

    mensaje = EmailMessage()
    mensaje["From"] = settings.MAIL_FROM_NAME + " <" + settings.MAIL_ADDRESS + ">"
    mensaje["To"] = fila.destinatario_valor
    mensaje["Subject"] = fila.asunto or "Notificación GeoTrack"
    mensaje.set_content(fila.cuerpo)
    mensaje.add_alternative(
        renderizar_email(fila.asunto, fila.cuerpo, fila.evento),
        subtype="html",
    )

    contexto = ssl.create_default_context()
    if settings.SMTP_PORT == 465:
        servidor = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20, context=contexto)
    else:
        servidor = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20)
    with servidor as smtp:
        if settings.SMTP_PORT != 465:
            smtp.starttls(context=contexto)
        smtp.login(settings.MAIL_ADDRESS, settings.MAIL_PASSWORD)
        smtp.send_message(mensaje)


def _enviar_telegram(fila) -> None:
    if not settings.TELEGRAM_BOT_TOKEN:
        raise RuntimeError("Telegram no está configurado: falta TELEGRAM_BOT_TOKEN")

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": fila.destinatario_valor, "text": fila.cuerpo}

    # Si es un mensaje de auxilio para el mecánico, añadir botones interactivos VOY / NO PUEDO
    if fila.evento == "AYUDA_ASIGNADA":
        payload["reply_markup"] = {
            "inline_keyboard": [
                [
                    {"text": "✅ VOY", "callback_data": f"VOY:{fila.clave_idempotencia}"},
                    {"text": "❌ NO PUEDO", "callback_data": f"NO_PUEDO:{fila.clave_idempotencia}"},
                ]
            ]
        }

    datos = json.dumps(payload).encode("utf-8")
    solicitud = Request(url, data=datos, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(solicitud, timeout=20) as respuesta:  # nosec B310
            resultado = json.loads(respuesta.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(f"Error de Telegram: {exc}") from exc
    if not resultado.get("ok"):
        raise RuntimeError(f"Telegram rechazó el mensaje: {resultado}")


def _enviar_whatsapp(fila) -> None:
    """Adaptador listo para WhatsApp Cloud API (Graph API de Meta)."""
    token = getattr(settings, "WHATSAPP_TOKEN", "").strip()
    phone_id = getattr(settings, "WHATSAPP_PHONE_ID", "").strip()
    if not token or not phone_id:
        raise RuntimeError("WhatsApp Cloud API no está configurada (WHATSAPP_TOKEN / WHATSAPP_PHONE_ID)")

    url = f"https://graph.facebook.com/v19.0/{phone_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": fila.destinatario_valor,
        "type": "text",
        "text": {"preview_url": True, "body": fila.cuerpo},
    }
    datos = json.dumps(payload).encode("utf-8")
    solicitud = Request(
        url,
        data=datos,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
        method="POST"
    )
    try:
        with urlopen(solicitud, timeout=20) as respuesta:  # nosec B310
            resultado = json.loads(respuesta.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(f"Error de WhatsApp API: {exc}") from exc
    if "messages" not in resultado:
        raise RuntimeError(f"WhatsApp API devolvió respuesta no exitosa: {resultado}")
