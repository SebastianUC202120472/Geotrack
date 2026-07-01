import imaplib
import smtplib
import re
from datetime import datetime, timezone
from email import message_from_bytes
from email.header import decode_header, make_header
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import parseaddr, parsedate_to_datetime, make_msgid, formataddr
import os

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories import correo_repository
from app.services import notificaciones_service

_PREFIJOS = re.compile(r"^\s*(re|rv|fwd|fw)\s*:\s*", re.IGNORECASE)


def _configurado() -> bool:
    return bool(settings.MAIL_ENABLED and settings.MAIL_ADDRESS and settings.MAIL_PASSWORD)


def _exigir_configurado():
    if not _configurado():
        raise HTTPException(
            status_code=400,
            detail="El correo de la empresa no está configurado. Completa las variables MAIL_* en el .env.",
        )


def _decodificar(valor: str | None) -> str:
    """Decodifica encabezados MIME. Recibe el valor crudo del encabezado."""
    if not valor:
        return ""
    try:
        return str(make_header(decode_header(valor)))
    except Exception:
        return valor


def _normalizar_asunto(asunto: str) -> str:
    """Quita prefijos Re/Fwd del asunto para agrupar el hilo. Recibe el asunto crudo."""
    limpio = asunto or "(sin asunto)"
    anterior = None
    while anterior != limpio:
        anterior = limpio
        limpio = _PREFIJOS.sub("", limpio).strip()
    return limpio or "(sin asunto)"


def _fecha(msg) -> datetime:
    try:
        dt = parsedate_to_datetime(msg.get("Date"))
        if dt.tzinfo:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt
    except Exception:
        return datetime.utcnow()


def _cuerpo(msg) -> str:
    """Extrae el texto plano del correo. Recibe el objeto message."""
    if msg.is_multipart():
        for parte in msg.walk():
            if parte.get_content_type() == "text/plain" and "attachment" not in str(parte.get("Content-Disposition")):
                carga = parte.get_payload(decode=True)
                if carga:
                    return carga.decode(parte.get_content_charset() or "utf-8", errors="replace").strip()
        return ""
    carga = msg.get_payload(decode=True)
    if carga:
        return carga.decode(msg.get_content_charset() or "utf-8", errors="replace").strip()
    return ""


def _adjuntos(msg):
    """Devuelve lista de adjuntos como (nombre, content_type, bytes). Recibe el objeto message."""
    encontrados = []
    if not msg.is_multipart():
        return encontrados
    for parte in msg.walk():
        if parte.get_content_maintype() == "multipart":
            continue
        nombre = parte.get_filename()
        disposicion = str(parte.get("Content-Disposition") or "")
        if nombre or "attachment" in disposicion.lower():
            carga = parte.get_payload(decode=True)
            if carga:
                encontrados.append((
                    _decodificar(nombre) or "adjunto",
                    parte.get_content_type(),
                    carga,
                ))
    return encontrados


def sincronizar(db: Session) -> dict:
    """Lee la bandeja por IMAP e importa correos entrantes nuevos. Recibe la sesion de BD."""
    if not _configurado():
        return {"mensaje": "El correo no está configurado todavía.", "nuevos": 0}

    try:
        imap = imaplib.IMAP4_SSL(settings.IMAP_HOST, settings.IMAP_PORT)
        imap.login(settings.MAIL_ADDRESS, settings.MAIL_PASSWORD)
        imap.select(settings.MAIL_FOLDER)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"No se pudo conectar al correo (IMAP): {e}")

    nuevos = 0
    try:
        estado, datos = imap.search(None, "UNSEEN")
        ids = datos[0].split() if datos and datos[0] else []
        for num in ids[-50:]:
            estado, bruto = imap.fetch(num, "(RFC822)")
            if estado != "OK" or not bruto or not bruto[0]:
                continue
            msg = message_from_bytes(bruto[0][1])

            message_id = (msg.get("Message-ID") or "").strip()
            if correo_repository.existe_mensaje(db, message_id):
                continue

            nombre, correo_origen = parseaddr(msg.get("From", ""))
            asunto = _decodificar(msg.get("Subject"))
            conv = correo_repository.buscar_o_crear_conversacion(
                db,
                contraparte_email=correo_origen or "desconocido",
                asunto=asunto,
                asunto_normalizado=_normalizar_asunto(asunto),
                nombre=_decodificar(nombre) or None,
            )
            mensaje = correo_repository.agregar_mensaje(
                db, conv,
                direccion="ENTRANTE",
                remitente=correo_origen or "desconocido",
                destinatario=settings.MAIL_ADDRESS,
                asunto=asunto,
                cuerpo=_cuerpo(msg),
                fecha=_fecha(msg),
                message_id=message_id or None,
                in_reply_to=(msg.get("In-Reply-To") or "").strip() or None,
                leido=False,
            )
            for nombre_adj, tipo_adj, datos_adj in _adjuntos(msg):
                correo_repository.agregar_adjunto(db, mensaje, nombre_adj, tipo_adj, datos_adj)
            conv.no_leidos = (conv.no_leidos or 0) + 1
            conv.estado = "PENDIENTE"
            nuevos += 1
            try:
                notificaciones_service.registrar(
                    db, "correos", "Nuevo correo entrante",
                    f"De: {correo_origen or 'desconocido'} — {asunto or '(sin asunto)'}", "/bandeja", conv.id)
            except Exception:
                pass

        db.commit()
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=502, detail=f"Error leyendo la bandeja: {e}")
    finally:
        try:
            imap.logout()
        except Exception:
            pass

    return {"mensaje": f"Sincronización completa. {nuevos} correo(s) nuevo(s).", "nuevos": nuevos}


def responder(db: Session, conversacion_id: int, cuerpo: str, admin_id: int | None = None) -> dict:
    """Envia la respuesta del admin por SMTP y la guarda en el hilo. Recibe id de conversacion y cuerpo."""
    _exigir_configurado()
    conv = correo_repository.obtener_conversacion(db, conversacion_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    if not cuerpo or not cuerpo.strip():
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío")

    asunto = conv.asunto if conv.asunto.lower().startswith("re:") else f"Re: {conv.asunto}"

    cuerpo_final = f"{cuerpo.strip()}\n\n--\n{settings.firma}"

    ultimo_entrante = next(
        (m for m in reversed(conv.mensajes) if m.direccion == "ENTRANTE" and m.message_id), None
    )
    in_reply_to = ultimo_entrante.message_id if ultimo_entrante else None

    mensaje = MIMEText(cuerpo_final, "plain", "utf-8")
    mensaje["From"] = formataddr((settings.MAIL_FROM_NAME, settings.MAIL_ADDRESS))
    mensaje["To"] = conv.contraparte_email
    mensaje["Subject"] = asunto
    nuevo_id = make_msgid()
    mensaje["Message-ID"] = nuevo_id
    if in_reply_to:
        mensaje["In-Reply-To"] = in_reply_to
        mensaje["References"] = in_reply_to

    try:
        if settings.SMTP_PORT == 465:
            servidor = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20)
        else:
            servidor = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20)
            servidor.starttls()
        servidor.login(settings.MAIL_ADDRESS, settings.MAIL_PASSWORD)
        servidor.send_message(mensaje)
        servidor.quit()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"No se pudo enviar el correo (SMTP): {e}")

    correo_repository.agregar_mensaje(
        db, conv,
        direccion="SALIENTE",
        remitente=settings.MAIL_ADDRESS,
        destinatario=conv.contraparte_email,
        asunto=asunto,
        cuerpo=cuerpo_final,
        fecha=datetime.utcnow(),
        message_id=nuevo_id,
        in_reply_to=in_reply_to,
        leido=True,
        enviado_por=admin_id,
    )
    conv.estado = "ATENDIDA"
    db.commit()
    return {"mensaje": "Respuesta enviada correctamente."}


def enviar_confirmacion_recojo(db, conversacion, num_pedidos, admin_id=None):
    """Envia correo HTML de confirmacion de recojo al cliente. Recibe conversacion, num_pedidos y admin_id. Best-effort."""
    if not _configurado():
        return
    asunto = f"Recibimos su solicitud de recojo ({num_pedidos} pedidos)"
    texto = (
        f"Estimado cliente,\n\nRecibimos su solicitud de recojo de {num_pedidos} pedidos. "
        "Ya está siendo procesada y coordinaremos el recojo en su almacén; le informaremos "
        "los siguientes pasos.\n\nAtentamente,\nSAVA S.A.C — Equipo de Logística"
    )
    html = (
        "<div style=\"font-family:Arial,sans-serif;color:#1f2733;font-size:14px\">"
        "<p>Estimado cliente,</p>"
        f"<p>Recibimos su <b>solicitud de recojo de {num_pedidos} pedidos</b>. Ya está siendo "
        "procesada y coordinaremos el recojo en su almacén; le informaremos los siguientes pasos.</p>"
        "<p>Atentamente,</p>"
        "<table style=\"border-collapse:collapse\"><tr>"
        "<td><img src=\"cid:logo\" alt=\"SAVA\" height=\"46\"></td>"
        "<td style=\"padding-left:10px\"><b>SAVA S.A.C</b><br>"
        "<span style=\"color:#64748b\">Equipo de Logística</span></td>"
        "</tr></table></div>"
    )
    raiz = MIMEMultipart("related")
    raiz["From"] = formataddr((settings.MAIL_FROM_NAME, settings.MAIL_ADDRESS))
    raiz["To"] = conversacion.contraparte_email
    raiz["Subject"] = asunto
    nuevo_id = make_msgid()
    raiz["Message-ID"] = nuevo_id
    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(texto, "plain", "utf-8"))
    alt.attach(MIMEText(html, "html", "utf-8"))
    raiz.attach(alt)
    ruta_logo = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "logo.png")
    try:
        with open(ruta_logo, "rb") as f:
            img = MIMEImage(f.read())
            img.add_header("Content-ID", "<logo>")
            img.add_header("Content-Disposition", "inline", filename="logo.png")
            raiz.attach(img)
    except OSError:
        pass
    try:
        if settings.SMTP_PORT == 465:
            servidor = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20)
        else:
            servidor = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20)
            servidor.starttls()
        servidor.login(settings.MAIL_ADDRESS, settings.MAIL_PASSWORD)
        servidor.send_message(raiz)
        servidor.quit()
    except Exception:
        return
    try:
        correo_repository.agregar_mensaje(
            db, conversacion,
            direccion="SALIENTE",
            remitente=settings.MAIL_ADDRESS,
            destinatario=conversacion.contraparte_email,
            asunto=asunto,
            cuerpo=texto,
            fecha=datetime.utcnow(),
            message_id=nuevo_id,
            leido=True,
            enviado_por=admin_id,
        )
        db.commit()
    except Exception:
        db.rollback()


def listar(db: Session):
    return correo_repository.listar_conversaciones(db)


def obtener_detalle(db: Session, conversacion_id: int):
    conv = correo_repository.obtener_conversacion(db, conversacion_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    correo_repository.marcar_leida(db, conv)
    return conv


def obtener_adjunto(db: Session, adjunto_id: int):
    adjunto = correo_repository.obtener_adjunto(db, adjunto_id)
    if not adjunto:
        raise HTTPException(status_code=404, detail="Adjunto no encontrado")
    return adjunto


def cambiar_estado(db: Session, conversacion_id: int, estado: str):
    estado = (estado or "").upper()
    if estado not in {"PENDIENTE", "ATENDIDA"}:
        raise HTTPException(status_code=400, detail="Estado inválido (PENDIENTE | ATENDIDA)")
    conv = correo_repository.obtener_conversacion(db, conversacion_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    return correo_repository.cambiar_estado(db, conv, estado)
