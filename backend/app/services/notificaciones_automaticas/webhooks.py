# Webhooks de mensajeria (Telegram y WhatsApp Cloud API).
# Seguridad: solo se procesa lo que de verdad manda el proveedor (secret_token de Telegram y
# firma X-Hub-Signature-256 de Meta); vincular un chat exige un token firmado que entrega el
# portal tras verificar codigo + DNI; "VOY" solo cuenta si lo responde el mecanico asignado.
# Las respuestas al usuario se encolan como avisos: el notificador las envia.
import hashlib
import hmac
import re
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories import notificacion_automatica_repository as repo
from app.repositories import notificacion_envio_repository, ruta_repository
from app.services.notificaciones_automaticas import destinatarios as dest
from app.services.notificaciones_automaticas import operador, vinculos
from app.services.notificaciones_automaticas.constructor import _correo
from app.services.notificaciones_automaticas.modelos import Canal, Destinatario, Mensaje, Prioridad

_PATRON_ASIGNADA = re.compile(r"^AYUDA_ASIGNADA:([A-Za-z0-9-]{1,20}):(\d{1,9})$")


# --- Verificacion del remitente ---

def verificar_telegram(cabecera: str | None) -> bool:
    """True si la llamada trae el secret_token configurado en setWebhook. Recibe la cabecera."""
    secreto = settings.TELEGRAM_WEBHOOK_SECRET or ""
    return bool(secreto and cabecera) and hmac.compare_digest(cabecera, secreto)


def verificar_firma_whatsapp(cuerpo: bytes, cabecera: str | None) -> bool:
    """True si X-Hub-Signature-256 corresponde al cuerpo exacto. Recibe el cuerpo crudo y la cabecera."""
    secreto = settings.WHATSAPP_APP_SECRET or ""
    if not secreto or not cabecera or not cabecera.startswith("sha256="):
        return False
    esperada = hmac.new(secreto.encode(), cuerpo, hashlib.sha256).hexdigest()
    return hmac.compare_digest(cabecera[len("sha256="):], esperada)


def verificar_handshake(modo: str | None, token: str | None) -> bool:
    """True si Meta registra el webhook con el token acordado. Recibe hub.mode y hub.verify_token."""
    esperado = settings.WHATSAPP_VERIFY_TOKEN or ""
    return modo == "subscribe" and bool(esperado and token) and hmac.compare_digest(token, esperado)


# --- Utilidades ---

def _responder(db: Session, canal: Canal, valor: str, cuerpo: str, clave: str) -> None:
    """Encola una respuesta corta al chat o telefono. Recibe canal, destino, texto y clave unica."""
    notificacion_envio_repository.crear_si_no_existe(db, Mensaje(
        evento="RESPUESTA_BOT", canal=canal, destinatario=Destinatario("respuesta", valor),
        cuerpo=cuerpo, clave_idempotencia=clave[:120], prioridad=Prioridad.URGENTE,
    ))


def _ultimos_digitos(telefono: str | None) -> str:
    """Los ultimos 9 digitos de un telefono, para comparar +51 987... con 987... Recibe el telefono."""
    return re.sub(r"\D", "", telefono or "")[-9:]


def _mecanico_por_telefono(db: Session, telefono: str):
    """Mecanico verificado cuyo telefono coincide (sin importar el prefijo). Recibe el telefono."""
    buscado = _ultimos_digitos(telefono)
    if len(buscado) < 9:
        return None
    return next((m for m in repo.mecanicos_verificados(db) if _ultimos_digitos(m.telefono_whatsapp) == buscado), None)


def _incidencia_asignada(db: Session, mecanico) -> tuple:
    """La incidencia ABIERTA mas reciente asignada a ese mecanico, con su clave. Recibe el mecanico."""
    claves = [c for c in repo.claves_con_prefijo(db, "AYUDA_ASIGNADA:") if c.endswith(f":{mecanico.id}")]
    for clave in reversed(claves):
        m = _PATRON_ASIGNADA.match(clave)
        inc = repo.obtener_incidencia_por_codigo(db, m.group(1)) if m else None
        if inc is not None and inc.estado == "ABIERTA":
            return inc, clave
    return None, None


def _ayuda_en_camino(db: Session, inc, mecanico) -> int:
    """Avisa al conductor que el mecanico confirmo que va. Recibe la incidencia y el mecanico."""
    ruta = ruta_repository.obtener_ruta_por_id(db, inc.ruta_id)
    return operador.registrar(db, "AYUDA_EN_CAMINO", {
        "incidencia": inc,
        "conductor_id": ruta.conductor_id if ruta else inc.conductor_id,
        "mecanico_nombre": mecanico.nombre,
        "mecanico_taller": mecanico.empresa_taller or "",
        "mecanico_telefono": mecanico.telefono_whatsapp,
    })


def _avisar_rechazo(db: Session, inc, mecanico) -> None:
    """Correo urgente al administrador cuando el mecanico responde NO PUEDO. Recibe incidencia y mecanico."""
    msg = _correo(
        "AUXILIO_MECANICO", "administrador", dest.email_admin(),
        f"ALERTA: el mecánico rechazó el auxilio {inc.codigo}",
        f"{mecanico.nombre} respondió 'NO PUEDO' al auxilio {inc.codigo}.\n"
        f"Entra a Auxilio Mecánico para asignar al siguiente mecánico más cercano.",
        f"RECHAZO_MECANICO:{inc.codigo}:{mecanico.id}", prioridad=Prioridad.URGENTE,
    )
    if msg:
        notificacion_envio_repository.crear_si_no_existe(db, msg)
    db.commit()


def _vincular(db: Session, canal: Canal, valor: str, token: str, nombre: str | None) -> bool:
    """Liga el chat al pedido o conductor del token firmado. Recibe canal, chat, token y nombre."""
    leido = vinculos.leer_token(token)
    if leido is None:
        return False
    entidad_tipo, entidad_id = leido
    repo.guardar_contacto(db, entidad_tipo, entidad_id, canal.value, valor, nombre)
    repo.quitar_baja(db, canal.value, valor)  # volver a suscribirse es un consentimiento nuevo
    _responder(db, canal, valor,
               "Listo: te avisaremos por aquí cada avance. Escribe STOP para dejar de recibir mensajes.",
               f"VINCULO:{entidad_tipo}:{entidad_id}:{valor}")
    db.commit()
    return True


def _baja(db: Session, canal: Canal, valor: str) -> None:
    """Registra STOP y desactiva los contactos de ese chat o telefono. Recibe canal y valor."""
    repo.registrar_baja(db, canal.value, valor, "STOP")
    repo.desactivar_contactos_por_valor(db, canal.value, valor)
    db.commit()


def _ayuda(db: Session, canal: Canal, valor: str) -> None:
    """Responde AYUDA con el enlace al portal (una vez por hora). Recibe canal y valor."""
    _responder(db, canal, valor, f"Para rastrear tu pedido o reprogramarlo entra a: {dest.enlace_portal()}",
               f"AYUDA:{canal.value}:{valor}:{datetime.utcnow():%Y%m%d%H}")
    db.commit()


# --- Telegram ---

def procesar_telegram(db: Session, payload: dict) -> dict:
    """Atiende /start <token>, STOP, AYUDA y los botones VOY / NO PUEDO. Recibe el JSON de Telegram."""
    callback = payload.get("callback_query")
    if callback:
        return _boton_telegram(db, callback)

    msg = payload.get("message") or {}
    texto = (msg.get("text") or "").strip()
    chat_id = str((msg.get("chat") or {}).get("id") or "")
    if not texto or not chat_id:
        return {"ok": True}

    if texto.startswith("/start"):
        partes = texto.split(maxsplit=1)
        nombre = (msg.get("from") or {}).get("first_name")
        vinculado = len(partes) == 2 and _vincular(db, Canal.TELEGRAM, chat_id, partes[1], nombre)
        return {"ok": True, "vinculado": bool(vinculado)}
    if texto.upper() == "STOP":
        _baja(db, Canal.TELEGRAM, chat_id)
        return {"ok": True, "baja": True}
    if texto.upper() == "AYUDA":
        _ayuda(db, Canal.TELEGRAM, chat_id)
        return {"ok": True, "ayuda": True}
    return {"ok": True}


def _boton_telegram(db: Session, callback: dict) -> dict:
    """Procesa VOY / NO PUEDO solo si quien pulsa es el mecanico asignado. Recibe el callback_query."""
    data = callback.get("data") or ""
    chat_id = str((callback.get("from") or {}).get("id") or "")
    accion, _, clave = data.partition(":")
    m = _PATRON_ASIGNADA.match(clave)
    mecanico = repo.obtener_mecanico_por_chat(db, chat_id) if chat_id else None
    if accion not in ("VOY", "NO_PUEDO") or not m or mecanico is None or str(mecanico.id) != m.group(2):
        return {"ok": True, "accion": "IGNORADA"}
    if not repo.existe_clave(db, clave):
        return {"ok": True, "accion": "IGNORADA"}
    inc = repo.obtener_incidencia_por_codigo(db, m.group(1))
    if inc is None or inc.estado != "ABIERTA":
        return {"ok": True, "accion": "IGNORADA"}
    if accion == "VOY":
        _ayuda_en_camino(db, inc, mecanico)
        return {"ok": True, "accion": "VOY_PROCESADO"}
    _avisar_rechazo(db, inc, mecanico)
    return {"ok": True, "accion": "NO_PUEDO_REGISTRADO"}


# --- WhatsApp ---

def procesar_whatsapp(db: Session, payload: dict) -> dict:
    """Atiende STOP, AYUDA, VOY y NO PUEDO que llegan por WhatsApp. Recibe el JSON de Meta."""
    for entrada in payload.get("entry") or []:
        for cambio in entrada.get("changes") or []:
            for msg in (cambio.get("value") or {}).get("messages") or []:
                _mensaje_whatsapp(db, str(msg.get("from") or ""), ((msg.get("text") or {}).get("body") or ""))
    return {"status": "ok"}


def _mensaje_whatsapp(db: Session, de: str, texto: str) -> None:
    """Procesa un mensaje de WhatsApp. Recibe el telefono del remitente y el texto."""
    texto = " ".join(texto.upper().replace("_", " ").split())
    if not de or not texto:
        return
    if texto == "STOP":
        _baja(db, Canal.WHATSAPP, de)
    elif texto == "AYUDA":
        _ayuda(db, Canal.WHATSAPP, de)
    elif texto in ("VOY", "NO PUEDO"):
        mecanico = _mecanico_por_telefono(db, de)
        inc, _ = _incidencia_asignada(db, mecanico) if mecanico else (None, None)
        if inc is None:
            return  # no es un mecanico con un auxilio asignado: se ignora
        if texto == "VOY":
            _ayuda_en_camino(db, inc, mecanico)
        else:
            _avisar_rechazo(db, inc, mecanico)
