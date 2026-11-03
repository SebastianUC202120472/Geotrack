"""Endpoints del Centro de Notificaciones:
- Historial interno de notificaciones admin (campana).
- Directorio de mecánicos (CRUD, geocodificación y verificación OTP).
- Bitácora de envíos externos (notificaciones_envios).
- Configuración de plantillas e interruptores.
- Webhooks de mensajería (Telegram y WhatsApp) con soporte STOP, AYUDA, VOY y NO PUEDO.
"""
import secrets
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_current_admin
from app.core.config import settings
from app.services import notificaciones_service
from app.schemas.notificacion import NotificacionesResponse, NotificacionContactoCreate
from app.schemas.notificacion_mecanico import MecanicoCreate, MecanicoUpdate, MecanicoVerificarOtp, PlantillaUpdate
from app.models.notificacion_contacto import NotificacionContacto
from app.models.notificacion_mecanico import NotificacionMecanico
from app.models.notificacion_envio import NotificacionEnvio
from app.models.notificacion_plantilla import NotificacionPlantilla, NotificacionBaja
from app.models.incidencia import Incidencia
from app.models.ruta import Ruta
from app.services.geocoder import obtener_coordenadas
from app.services.notificaciones_automaticas import operador
from app.services.notificaciones_automaticas.constructor import _telegram_pedido

router = APIRouter()


# ---------------------------------------------------------
# 1. Alertas internas del panel (Campana)
# ---------------------------------------------------------

@router.get("", response_model=NotificacionesResponse, dependencies=[Depends(get_current_admin)])
def listar_notificaciones(limite: int = 50, db: Session = Depends(get_db)):
    """Lista notificaciones internas del admin con contador de no vistas."""
    return notificaciones_service.listar(db, limite=max(1, min(limite, 500)))


@router.post("/marcar-vistas", dependencies=[Depends(get_current_admin)])
def marcar_vistas(db: Session = Depends(get_db)):
    """Marca todas las notificaciones internas como vistas."""
    return {"marcadas": notificaciones_service.marcar_vistas(db)}


# ---------------------------------------------------------
# 2. Bitácora de Envíos Externos (Outbox)
# ---------------------------------------------------------

@router.get("/envios", dependencies=[Depends(get_current_admin)])
def listar_envios(
    estado: Optional[str] = None,
    canal: Optional[str] = None,
    evento: Optional[str] = None,
    limite: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Consulta la bitácora de mensajes enviados, pendientes o fallidos con paginación y filtros."""
    q = db.query(NotificacionEnvio)
    if estado:
        q = q.filter(NotificacionEnvio.estado == estado.upper())
    if canal:
        q = q.filter(NotificacionEnvio.canal == canal.lower())
    if evento:
        q = q.filter(NotificacionEnvio.evento == evento.upper())

    total = q.count()
    filas = q.order_by(NotificacionEnvio.id.desc()).offset(offset).limit(limite).all()

    # Enmascarar destinatario para privacidad si es teléfono
    items = []
    for f in filas:
        valor = f.destinatario_valor or ""
        if len(valor) >= 7 and valor.replace("+", "").isdigit():
            valor_mask = valor[:3] + "****" + valor[-2:]
        else:
            valor_mask = valor
        items.append({
            "id": f.id,
            "evento": f.evento,
            "canal": f.canal,
            "destinatario_tipo": f.destinatario_tipo,
            "destinatario_valor": valor_mask,
            "destinatario_nombre": f.destinatario_nombre,
            "asunto": f.asunto,
            "cuerpo": f.cuerpo,
            "prioridad": f.prioridad,
            "estado": f.estado,
            "clave_idempotencia": f.clave_idempotencia,
            "intentos": f.intentos,
            "creado_en": f.creado_en.isoformat() if f.creado_en else None,
            "enviado_en": f.enviado_en.isoformat() if f.enviado_en else None,
            "detalle": f.detalle,
        })

    return {"total": total, "items": items}


@router.post("/envios/{envio_id}/reintentar", dependencies=[Depends(get_current_admin)])
def reintentar_envio(envio_id: int, db: Session = Depends(get_db)):
    """Reintenta manualmente un envío que quedó en estado FALLIDO."""
    envio = db.query(NotificacionEnvio).filter(NotificacionEnvio.id == envio_id).first()
    if not envio:
        raise HTTPException(status_code=404, detail="Envío no encontrado")
    envio.estado = "PENDIENTE"
    envio.intentos = 0
    envio.proximo_intento_en = None
    envio.bloqueado_hasta = None
    envio.detalle = "Reintento manual solicitado por administración"
    db.commit()
    return {"mensaje": "Envío reprogramado para entrega"}


# ---------------------------------------------------------
# 3. Directorio de Mecánicos y Auxilio
# ---------------------------------------------------------

@router.get("/mecanicos", dependencies=[Depends(get_current_admin)])
def listar_mecanicos(db: Session = Depends(get_db)):
    """Lista todos los mecánicos y proveedores de auxilio mecánico."""
    return db.query(NotificacionMecanico).order_by(NotificacionMecanico.nombre.asc()).all()


@router.post("/mecanicos", dependencies=[Depends(get_current_admin)])
def crear_mecanico(datos: MecanicoCreate, db: Session = Depends(get_db)):
    """Da de alta un mecánico, geocodifica su taller y deja pendiente la verificación de teléfono."""
    tel = datos.telefono_whatsapp.strip()
    existente = db.query(NotificacionMecanico).filter(NotificacionMecanico.telefono_whatsapp == tel).first()
    if existente:
        raise HTTPException(status_code=400, detail="Ya existe un mecánico con ese teléfono")

    lat, lon = datos.latitud, datos.longitud
    if (lat is None or lon is None) and datos.direccion:
        coords = obtener_coordenadas(db, datos.direccion)
        if coords:
            lat, lon = coords

    mecanico = NotificacionMecanico(
        nombre=datos.nombre.strip(),
        empresa_taller=datos.empresa_taller.strip() if datos.empresa_taller else None,
        tipo_servicio=datos.tipo_servicio,
        distritos=datos.distritos,
        direccion=datos.direccion,
        latitud=lat,
        longitud=lon,
        telefono_whatsapp=tel,
        telegram_chat_id=datos.telegram_chat_id.strip() if datos.telegram_chat_id else None,
        horario_inicio=datos.horario_inicio,
        horario_fin=datos.horario_fin,
        activo=datos.activo,
        telefono_verificado=False,
    )
    db.add(mecanico)
    db.commit()
    db.refresh(mecanico)
    return mecanico


@router.put("/mecanicos/{mecanico_id}", dependencies=[Depends(get_current_admin)])
def actualizar_mecanico(mecanico_id: int, datos: MecanicoUpdate, db: Session = Depends(get_db)):
    """Actualiza los datos del mecánico y vuelve a geocodificar si cambió la dirección."""
    mecanico = db.query(NotificacionMecanico).filter(NotificacionMecanico.id == mecanico_id).first()
    if not mecanico:
        raise HTTPException(status_code=404, detail="Mecánico no encontrado")

    if datos.direccion and datos.direccion != mecanico.direccion and (datos.latitud is None or datos.longitud is None):
        coords = obtener_coordenadas(db, datos.direccion)
        if coords:
            mecanico.latitud, mecanico.longitud = coords

    for campo, valor in datos.dict().items():
        if campo in ("latitud", "longitud") and valor is None:
            continue
        setattr(mecanico, campo, valor)

    db.commit()
    db.refresh(mecanico)
    return mecanico


@router.delete("/mecanicos/{mecanico_id}", dependencies=[Depends(get_current_admin)])
def eliminar_mecanico(mecanico_id: int, db: Session = Depends(get_db)):
    """Elimina a un mecánico del directorio."""
    mecanico = db.query(NotificacionMecanico).filter(NotificacionMecanico.id == mecanico_id).first()
    if not mecanico:
        raise HTTPException(status_code=404, detail="Mecánico no encontrado")
    db.delete(mecanico)
    db.commit()
    return {"mensaje": "Mecánico eliminado"}


@router.post("/mecanicos/{mecanico_id}/enviar-codigo", dependencies=[Depends(get_current_admin)])
def enviar_codigo_verificacion_mecanico(mecanico_id: int, db: Session = Depends(get_db)):
    """Genera y envía un código OTP de 6 dígitos al mecánico para verificar su número."""
    mecanico = db.query(NotificacionMecanico).filter(NotificacionMecanico.id == mecanico_id).first()
    if not mecanico:
        raise HTTPException(status_code=404, detail="Mecánico no encontrado")

    otp = f"{secrets.randbelow(900000) + 100000}"
    mecanico.codigo_verificacion = otp
    mecanico.codigo_expira_en = datetime.utcnow() + timedelta(minutes=15)
    db.commit()

    # Priorizar Telegram si está configurado el chat_id o si WhatsApp no está disponible
    from app.services.notificaciones_automaticas.modelos import Mensaje, Destinatario, Canal, Prioridad
    if mecanico.telegram_chat_id:
        destino = mecanico.telegram_chat_id
        canal = Canal.TELEGRAM
    elif getattr(settings, "WHATSAPP_TOKEN", "").strip():
        destino = mecanico.telefono_whatsapp
        canal = Canal.WHATSAPP
    else:
        # Modo Telegram demo sin chat_id: avisar al admin
        raise HTTPException(
            status_code=400,
            detail="Para la demo con Telegram ingresa el Chat ID de Telegram del mecánico para enviarle el código."
        )
    msg = Mensaje(
        evento="VERIFICACION_NUMERO",
        canal=canal,
        destinatario=Destinatario("mecanico", destino, mecanico.nombre),
        cuerpo=f"Hola {mecanico.nombre}, tu código de verificación para GeoTrack Auxilio Mecánico es: {otp}. Expira en 15 minutos.",
        clave_idempotencia=f"VERIFICACION_MECANICO:{mecanico.id}:{otp}",
        prioridad=Prioridad.URGENTE,
    )
    from app.repositories import notificacion_envio_repository
    notificacion_envio_repository.crear_si_no_existe(db, msg)
    db.commit()

    return {"mensaje": f"Código enviado al {destino} del mecánico"}


@router.post("/mecanicos/{mecanico_id}/verificar", dependencies=[Depends(get_current_admin)])
def verificar_mecanico(mecanico_id: int, datos: MecanicoVerificarOtp, db: Session = Depends(get_db)):
    """Verifica el código OTP ingresado por el mecánico o admin."""
    mecanico = db.query(NotificacionMecanico).filter(NotificacionMecanico.id == mecanico_id).first()
    if not mecanico:
        raise HTTPException(status_code=404, detail="Mecánico no encontrado")

    if not mecanico.codigo_verificacion or mecanico.codigo_verificacion != datos.codigo.strip():
        raise HTTPException(status_code=400, detail="Código de verificación incorrecto")

    if mecanico.codigo_expira_en and datetime.utcnow() > mecanico.codigo_expira_en:
        raise HTTPException(status_code=400, detail="El código de verificación ha expirado")

    mecanico.telefono_verificado = True
    mecanico.codigo_verificacion = None
    mecanico.codigo_expira_en = None
    db.commit()
    return {"mensaje": "Número de teléfono verificado exitosamente"}


@router.get("/mecanicos/propuesta/{incidencia_id}", dependencies=[Depends(get_current_admin)])
def proponer_mecanico_cercano(incidencia_id: int, tipo: Optional[str] = None, db: Session = Depends(get_db)):
    """Propone al mecánico activo, verificado y más cercano a la avería.
    Si un mecánico ya fue contactado para esta incidencia y no aceptó o venció, propone al siguiente."""
    from app.services.router import calcular_distancia

    inc = db.query(Incidencia).filter(Incidencia.id == incidencia_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")

    # IDs de mecánicos ya contactados previamente para esta avería
    prefijo = f"AYUDA_ASIGNADA:{inc.codigo}:"
    contactados_ids = set()
    envios_previos = db.query(NotificacionEnvio).filter(NotificacionEnvio.clave_idempotencia.like(f"{prefijo}%")).all()
    for ep in envios_previos:
        partes = ep.clave_idempotencia.split(":")
        if len(partes) >= 3 and partes[2].isdigit():
            contactados_ids.add(int(partes[2]))

    q = db.query(NotificacionMecanico).filter(
        NotificacionMecanico.activo.is_(True),
        NotificacionMecanico.telefono_verificado.is_(True),
    )
    if tipo:
        q = q.filter(NotificacionMecanico.tipo_servicio == tipo)

    todos = q.all()
    if not todos:
        raise HTTPException(status_code=404, detail="No hay mecánicos verificados para este servicio")

    # Filtrar no contactados primero para proponer al siguiente
    disponibles = [m for m in todos if m.id not in contactados_ids]
    candidatos_pool = disponibles if disponibles else todos

    lat_inc, lon_inc = inc.latitud, inc.longitud
    candidatos = []
    for m in candidatos_pool:
        dist_km = 999.0
        if lat_inc is not None and lon_inc is not None and m.latitud is not None and m.longitud is not None:
            dist_km = round(calcular_distancia(lat_inc, lon_inc, m.latitud, m.longitud), 2)
        candidatos.append({"mecanico": m, "distancia_km": dist_km})

    candidatos.sort(key=lambda x: x["distancia_km"])
    mejor = candidatos[0]["mecanico"]

    return {
        "mecanico_id": mejor.id,
        "nombre": mejor.nombre,
        "empresa_taller": mejor.empresa_taller,
        "telefono": mejor.telefono_whatsapp,
        "tipo_servicio": mejor.tipo_servicio,
        "distancia_km": candidatos[0]["distancia_km"] if candidatos[0]["distancia_km"] < 999 else None,
        "es_siguiente": len(contactados_ids) > 0,
    }


# ---------------------------------------------------------
# 4. Webhooks de Mensajería (Telegram y WhatsApp)
# ---------------------------------------------------------

@router.post("/webhook/telegram")
async def webhook_telegram(request: Request, db: Session = Depends(get_db)):
    """Recibe eventos y respuestas de Telegram (comandos /start, STOP, AYUDA, VOY, NO PUEDO)."""
    payload = await request.json()

    # Caso 1: Botón interactivo (Callback Query: VOY / NO PUEDO)
    callback = payload.get("callback_query")
    if callback:
        data = callback.get("data", "")
        chat_id = str(callback.get("from", {}).get("id"))
        if data.startswith("VOY:"):
            clave = data[4:]
            # Disparar aviso de ayuda en camino al conductor
            inc_codigo = clave.split(":")[1] if ":" in clave else ""
            inc = db.query(Incidencia).filter(Incidencia.codigo == inc_codigo).first()
            if inc:
                ruta = db.query(Ruta).filter(Ruta.id == inc.ruta_id).first()
                cond_id = ruta.conductor_id if ruta else inc.conductor_id
                mecanico = db.query(NotificacionMecanico).filter(NotificacionMecanico.telegram_chat_id == chat_id).first()
                operador.registrar(
                    db, "AYUDA_EN_CAMINO", {
                        "incidencia": inc,
                        "conductor_id": cond_id,
                        "mecanico_nombre": mecanico.nombre if mecanico else "Mecánico asignado",
                        "mecanico_taller": mecanico.empresa_taller if mecanico else "",
                        "mecanico_telefono": mecanico.telefono_whatsapp if mecanico else "",
                    }
                )
            return {"ok": True, "accion": "VOY_PROCESADO"}

        elif data.startswith("NO_PUEDO:"):
            clave = data[9:]
            inc_codigo = clave.split(":")[1] if ":" in clave else ""
            inc = db.query(Incidencia).filter(Incidencia.codigo == inc_codigo).first()
            mecanico = db.query(NotificacionMecanico).filter(NotificacionMecanico.telegram_chat_id == chat_id).first()
            nombre_mec = mecanico.nombre if mecanico else "El proveedor"
            # Notificar al administrador para que confirme al siguiente en el panel
            from app.services.notificaciones_automaticas.constructor import _correo
            from app.services.notificaciones_automaticas import destinatarios as dest
            from app.repositories import notificacion_envio_repository
            asunto = f"ALERTA: Mecánico rechazó auxilio {inc_codigo}"
            cuerpo = (
                f"{nombre_mec} respondió 'NO PUEDO' para atender el auxilio {inc_codigo}.\n"
                f"El sistema ha habilitado la propuesta del siguiente mecánico más cercano en el panel Auxilio Mecánico."
            )
            clave_alerta = f"RECHAZO_MECANICO:{inc_codigo}:{chat_id}"
            msg = _correo("AUXILIO_MECANICO", "administrador", dest.email_admin(), asunto, cuerpo, clave_alerta, prioridad=operador.Prioridad.URGENTE)
            if msg:
                notificacion_envio_repository.crear_si_no_existe(db, msg)
                db.commit()
            return {"ok": True, "accion": "NO_PUEDO_REGISTRADO", "propuesto_siguiente": True}

    # Caso 2: Mensaje de texto plano (/start, STOP, AYUDA)
    msg = payload.get("message", {})
    texto = (msg.get("text") or "").strip()
    chat_id = str(msg.get("chat", {}).get("id") or "")
    remitente_nombre = msg.get("from", {}).get("first_name", "")

    if not texto or not chat_id:
        return {"ok": True}

    # Comando /start con token de vinculación de pedido
    if texto.startswith("/start"):
        partes = texto.split()
        if len(partes) > 1 and partes[1].startswith("PD_"):
            pedido_codigo = partes[1][3:]
            # Vincular este chat_id al teléfono del pedido
            from app.models.pedido import Pedido
            pedido = db.query(Pedido).filter(Pedido.codigo == pedido_codigo).first()
            if pedido and pedido.telefono_destinatario:
                contacto = (
                    db.query(NotificacionContacto)
                    .filter(
                        NotificacionContacto.entidad_tipo == "telefono",
                        NotificacionContacto.entidad_id == pedido.id,
                        NotificacionContacto.canal == "telegram"
                    )
                    .first()
                )
                if not contacto:
                    contacto = NotificacionContacto(
                        entidad_tipo="telefono",
                        entidad_id=pedido.id,
                        canal="telegram",
                        valor=chat_id,
                        nombre=pedido.nombre_destinatario or remitente_nombre,
                        activo=True,
                    )
                    db.add(contacto)
                else:
                    contacto.valor = chat_id
                    contacto.activo = True
                db.commit()
                # Enviar confirmación al chat
                from app.services.notificaciones_automaticas.proveedores import _enviar_telegram
                from types import SimpleNamespace
                _enviar_telegram(SimpleNamespace(
                    canal="telegram",
                    destinatario_valor=chat_id,
                    cuerpo=f"¡Hola {remitente_nombre}! Vinculaste tus notificaciones para el pedido {pedido_codigo}. Te avisaremos en cada avance.",
                    evento="CONFIRMACION_VINCULACION",
                ))
        return {"ok": True}

    # Respuesta STOP: baja de consentimiento (Ley 29733)
    if texto.upper() == "STOP":
        db.add(NotificacionBaja(canal="telegram", valor=chat_id, motivo="STOP"))
        # Desactivar contactos asociados
        contactos = db.query(NotificacionContacto).filter(NotificacionContacto.valor == chat_id).all()
        for c in contactos:
            c.activo = False
        db.commit()
        return {"ok": True, "baja": True}

    # Respuesta AYUDA: enviar enlace al portal
    if texto.upper() == "AYUDA":
        from app.services.notificaciones_automaticas.proveedores import _enviar_telegram
        from types import SimpleNamespace
        portal_url = getattr(settings, "NOTIFICACIONES_URL_PORTAL", "https://sava.pe/portal")
        _enviar_telegram(SimpleNamespace(
            canal="telegram",
            destinatario_valor=chat_id,
            cuerpo=f"Para rastrear tu pedido o gestionar tu entrega ingresa a: {portal_url}",
            evento="AYUDA",
        ))
        return {"ok": True, "ayuda": True}

    return {"ok": True}


# ---------------------------------------------------------
# 5. Configuración de Plantillas y Switches
# ---------------------------------------------------------

    EVENTOS_DEFAULT = [
    ("PEDIDO_PROGRAMADO", "telegram", None, "Hola {nombre}, tu pedido {codigo} fue programado para hoy. Sigue su avance en {enlace_portal}"),
    ("PEDIDO_EN_CAMINO", "telegram", None, "Tu pedido {codigo} va en camino: eres la parada {secuencia} de {total}. Sigue su avance en {enlace_portal}"),
    ("PEDIDO_ESTA_CERCA", "telegram", None, "El repartidor está por llegar a tu dirección con tu pedido {codigo}. Sigue su avance en {enlace_portal}"),
    ("PEDIDO_ENTREGADO", "telegram", None, "Hola {nombre}, tu pedido {codigo} fue entregado con éxito. Verifica el comprobante en {enlace_portal}"),
    ("PEDIDO_NO_ENTREGADO", "telegram", None, "No pudimos entregar tu pedido {codigo}: {motivo}. Lo reprogramaremos; sigue su avance en {enlace_portal}"),
    ("PEDIDO_REPROGRAMADO", "telegram", None, "Tu pedido {codigo} fue reprogramado y saldrá en una nueva ruta. Sigue su avance en {enlace_portal}"),
    ("RECOJO_COMPLETADO", "correo", "Recojo {codigo} completado", "El recojo {codigo} de {cliente} fue completado con {cantidad} bultos."),
    ("PAQUETES_FALTANTES", "correo", "Paquetes faltantes en {codigo}", "En el ingreso del recojo {codigo} faltaron {n} paquetes: {faltantes}."),
    ("RETORNOS_ALMACEN", "correo", "Retornos al almacén — ruta {codigo_ruta}", "La ruta {codigo_ruta} terminó con {n} pedidos fallidos: {codigos}."),
    ("AUXILIO_MECANICO", "correo", "Auxilio mecánico {codigo}", "AUXILIO MECANICO — {codigo}\nVehículo: {placa}\nFalla: {descripcion}"),
    ("AYUDA_ASIGNADA", "telegram", None, "Te asignaron un auxilio {codigo}: vehículo {placa}. Responde VOY para aceptar."),
    ("AYUDA_EN_CAMINO", "telegram", None, "Tu auxilio {codigo} va en camino con {mecanico} ({telefono})."),
    ("RECLAMO_NUEVO", "correo", "Nuevo reclamo {codigo}", "Código: {codigo}\nTipo: {tipo}\nDetalle: {detalle}"),
    ("RESUMEN_DEL_DIA", "correo", "Resumen del día {fecha}", "Entregados: {entregados}\nFallidos: {fallidos}\nPendientes: {pendientes}"),
]


@router.get("/plantillas", dependencies=[Depends(get_current_admin)])
def listar_plantillas(db: Session = Depends(get_db)):
    """Lista las plantillas configuradas; si la tabla está vacía las inicializa con los valores estándar."""
    plantillas = db.query(NotificacionPlantilla).all()
    if not plantillas:
        for ev, can, asu, cue in EVENTOS_DEFAULT:
            db.add(NotificacionPlantilla(evento=ev, canal=can, asunto=asu, cuerpo=cue, activo=True))
        db.commit()
        plantillas = db.query(NotificacionPlantilla).all()
    return plantillas


@router.put("/plantillas/{plantilla_id}", dependencies=[Depends(get_current_admin)])
def actualizar_plantilla(plantilla_id: int, datos: PlantillaUpdate, db: Session = Depends(get_db)):
    """Actualiza el cuerpo, asunto o estado activo/inactivo de una plantilla."""
    p = db.query(NotificacionPlantilla).filter(NotificacionPlantilla.id == plantilla_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    p.cuerpo = datos.cuerpo
    p.asunto = datos.asunto
    p.activo = datos.activo
    db.commit()
    db.refresh(p)
    return p


# ---------------------------------------------------------
# 6. Webhook Oficial WhatsApp Cloud API (Meta)
# ---------------------------------------------------------

@router.get("/webhook/whatsapp")
def verificar_webhook_whatsapp(
    request: Request,
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_token: Optional[str] = Query(None, alias="hub.verify_token"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
):
    """Verificación handshake requerida por Meta al registrar el Webhook en App Dashboard."""
    token_esperado = getattr(settings, "WHATSAPP_VERIFY_TOKEN", "geotrack_webhook_secret")
    if hub_mode == "subscribe" and hub_token == token_esperado:
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(content=hub_challenge)
    raise HTTPException(status_code=403, detail="Token de verificación incorrecto")


@router.post("/webhook/whatsapp")
async def recibir_webhook_whatsapp(request: Request, db: Session = Depends(get_db)):
    """Recibe eventos de WhatsApp Cloud API (respuestas STOP, AYUDA, VOY, NO PUEDO)."""
    payload = await request.json()
    entries = payload.get("entry", [])
    for entry in entries:
        for change in entry.get("changes", []):
            valor = change.get("value", {})
            for msg in valor.get("messages", []):
                de = msg.get("from", "")  # teléfono del remitente E.164
                texto = (msg.get("text", {}).get("body") or "").strip().upper()

                if texto == "STOP":
                    db.add(NotificacionBaja(canal="whatsapp", valor=de, motivo="STOP"))
                    contactos = db.query(NotificacionContacto).filter(NotificacionContacto.valor == de).all()
                    for c in contactos:
                        c.activo = False
                    db.commit()

                elif texto == "AYUDA":
                    portal_url = getattr(settings, "NOTIFICACIONES_URL_PORTAL", "https://sava.pe/portal")
                    from app.services.notificaciones_automaticas.proveedores import _enviar_whatsapp
                    from types import SimpleNamespace
                    _enviar_whatsapp(SimpleNamespace(
                        canal="whatsapp",
                        destinatario_valor=de,
                        cuerpo=f"Para rastrear tu pedido o gestionar tu entrega ingresa a: {portal_url}",
                        evento="AYUDA",
                    ))

                elif texto == "VOY":
                    # Buscar mecánico con este teléfono
                    mecanico = db.query(NotificacionMecanico).filter(NotificacionMecanico.telefono_whatsapp == de).first()
                    inc = (
                        db.query(Incidencia)
                        .filter(Incidencia.estado == "ABIERTA", Incidencia.ayuda_enviada_en.isnot(None))
                        .order_by(Incidencia.id.desc())
                        .first()
                    )
                    if inc:
                        ruta = db.query(Ruta).filter(Ruta.id == inc.ruta_id).first()
                        cond_id = ruta.conductor_id if ruta else inc.conductor_id
                        operador.registrar(
                            db, "AYUDA_EN_CAMINO", {
                                "incidencia": inc,
                                "conductor_id": cond_id,
                                "mecanico_nombre": mecanico.nombre if mecanico else "Mecánico asignado",
                                "mecanico_taller": mecanico.empresa_taller if mecanico else "",
                                "mecanico_telefono": de,
                            }
                        )

                elif texto == "NO_PUEDO":
                    # Registrar rechazo para que el planificador o admin asigne al siguiente
                    log.info("Mecánico con teléfono %s respondió NO PUEDO", de)

    return {"status": "ok"}

