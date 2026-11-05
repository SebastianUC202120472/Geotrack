# Administracion del centro de notificaciones desde el panel: bitacora de envios, directorio de
# mecanicos (alta, verificacion y asignacion de un auxilio), plantillas y enlaces de Telegram.
import hmac
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.notificacion_mecanico import NotificacionMecanico
from app.models.notificacion_plantilla import NotificacionPlantilla
from app.repositories import conductor_repository, incidencia_repository, usuario_repository
from app.repositories import notificacion_automatica_repository as repo
from app.repositories import notificacion_envio_repository
from app.services.geocoder import obtener_coordenadas
from app.services.notificaciones_automaticas import operador, vinculos
from app.services.notificaciones_automaticas.modelos import Canal, Destinatario, Mensaje, Prioridad
from app.services.router import calcular_distancia

# Plantillas de fabrica: (evento, canal, asunto, cuerpo). Las variables entre llaves se
# reemplazan al armar cada aviso (ver constructor._variables).
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
    ("AYUDA_ASIGNADA", "telegram", None, "Te asignaron un auxilio {codigo}: vehículo {placa}, falla: {descripcion}. Conductor: {conductor}. Responde VOY para aceptar o NO PUEDO."),
    ("AYUDA_EN_CAMINO", "telegram", None, "Tu auxilio {codigo} va en camino con {mecanico} ({telefono})."),
    ("RECLAMO_NUEVO", "correo", "Nuevo reclamo {codigo}", "Código: {codigo}\nTipo: {tipo}\nDetalle: {detalle}"),
    ("RESUMEN_DEL_DIA", "correo", "Resumen del día {fecha}", "Entregados: {entregados}\nFallidos: {fallidos}\nPendientes: {pendientes}"),
]


def _enmascarar(valor: str) -> str:
    """Oculta el centro de un telefono o chat numerico. Recibe el valor."""
    valor = valor or ""
    if len(valor) >= 7 and valor.replace("+", "").replace("-", "").isdigit():
        return valor[:3] + "****" + valor[-2:]
    return valor


def _mecanico(db: Session, mecanico_id: int) -> NotificacionMecanico:
    """El mecanico o 404. Recibe el id."""
    mecanico = repo.obtener_mecanico(db, mecanico_id)
    if mecanico is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Mecánico no encontrado")
    return mecanico


# --- Bitacora de envios ---

def listar_envios(db: Session, estado: Optional[str], canal: Optional[str], evento: Optional[str],
                  limite: int, offset: int) -> dict:
    """Pagina de la bitacora con el destino enmascarado. Recibe filtros, limite y offset."""
    total, filas = repo.listar_envios(db, estado, canal, evento, limite, offset)
    items = [{
        "id": f.id, "evento": f.evento, "canal": f.canal, "destinatario_tipo": f.destinatario_tipo,
        "destinatario_valor": _enmascarar(f.destinatario_valor), "destinatario_nombre": f.destinatario_nombre,
        "asunto": f.asunto, "cuerpo": f.cuerpo, "prioridad": f.prioridad, "estado": f.estado,
        "clave_idempotencia": f.clave_idempotencia, "intentos": f.intentos,
        "creado_en": f.creado_en.isoformat() if f.creado_en else None,
        "enviado_en": f.enviado_en.isoformat() if f.enviado_en else None, "detalle": f.detalle,
    } for f in filas]
    return {"total": total, "items": items}


def reintentar_envio(db: Session, envio_id: int) -> dict:
    """Vuelve a poner en cola un envio fallido. Recibe el id."""
    envio = repo.obtener_envio(db, envio_id)
    if envio is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Envío no encontrado")
    envio.estado, envio.intentos = "PENDIENTE", 0
    envio.proximo_intento_en = envio.bloqueado_hasta = None
    envio.detalle = "Reintento manual solicitado por administración"
    db.commit()
    return {"mensaje": "Envío reprogramado para entrega"}


# --- Directorio de mecanicos ---

def listar_mecanicos(db: Session) -> list:
    """Todos los mecanicos. Sin input extra."""
    return repo.listar_mecanicos(db)


def crear_mecanico(db: Session, datos) -> NotificacionMecanico:
    """Alta de un mecanico con su taller geocodificado; el numero queda sin verificar. Recibe los datos."""
    telefono = datos.telefono_whatsapp.strip()
    if repo.obtener_mecanico_por_telefono(db, telefono):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Ya existe un mecánico con ese teléfono")
    lat, lon = datos.latitud, datos.longitud
    if (lat is None or lon is None) and datos.direccion:
        lat, lon = obtener_coordenadas(db, datos.direccion) or (lat, lon)
    mecanico = NotificacionMecanico(
        nombre=datos.nombre.strip(),
        empresa_taller=datos.empresa_taller.strip() if datos.empresa_taller else None,
        tipo_servicio=datos.tipo_servicio, distritos=datos.distritos, direccion=datos.direccion,
        latitud=lat, longitud=lon, telefono_whatsapp=telefono,
        telegram_chat_id=datos.telegram_chat_id.strip() if datos.telegram_chat_id else None,
        horario_inicio=datos.horario_inicio, horario_fin=datos.horario_fin, activo=datos.activo,
        telefono_verificado=False,
    )
    repo.guardar(db, mecanico)
    db.commit()
    db.refresh(mecanico)
    return mecanico


def actualizar_mecanico(db: Session, mecanico_id: int, datos) -> NotificacionMecanico:
    """Edita un mecanico; si cambia su telefono o su chat, vuelve a pedir verificacion. Recibe id y datos."""
    mecanico = _mecanico(db, mecanico_id)
    cambios = datos.model_dump()
    telefono = (cambios.get("telefono_whatsapp") or "").strip()
    otro = repo.obtener_mecanico_por_telefono(db, telefono) if telefono else None
    if otro is not None and otro.id != mecanico.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Ya existe un mecánico con ese teléfono")
    chat = (cambios.get("telegram_chat_id") or "").strip() or None
    if telefono != mecanico.telefono_whatsapp or chat != mecanico.telegram_chat_id:
        mecanico.telefono_verificado = False
    if (cambios.get("direccion") and cambios["direccion"] != mecanico.direccion
            and (cambios.get("latitud") is None or cambios.get("longitud") is None)):
        coords = obtener_coordenadas(db, cambios["direccion"])
        if coords:
            mecanico.latitud, mecanico.longitud = coords
    cambios.update(telefono_whatsapp=telefono, telegram_chat_id=chat)
    for campo, valor in cambios.items():
        if campo in ("latitud", "longitud") and valor is None:
            continue
        setattr(mecanico, campo, valor)
    db.commit()
    db.refresh(mecanico)
    return mecanico


def eliminar_mecanico(db: Session, mecanico_id: int) -> dict:
    """Quita a un mecanico del directorio. Recibe el id."""
    repo.eliminar(db, _mecanico(db, mecanico_id))
    db.commit()
    return {"mensaje": "Mecánico eliminado"}


def enviar_codigo(db: Session, mecanico_id: int) -> dict:
    """Genera un codigo de 6 digitos (15 min) y lo encola hacia el mecanico. Recibe el id."""
    mecanico = _mecanico(db, mecanico_id)
    if mecanico.telegram_chat_id:
        destino, canal = mecanico.telegram_chat_id, Canal.TELEGRAM
    elif (settings.WHATSAPP_TOKEN or "").strip():
        destino, canal = mecanico.telefono_whatsapp, Canal.WHATSAPP
    else:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "Ingresa el chat de Telegram del mecánico para enviarle el código.")
    codigo = f"{secrets.randbelow(900000) + 100000}"
    mecanico.codigo_verificacion = codigo
    mecanico.codigo_expira_en = datetime.utcnow() + timedelta(minutes=15)
    notificacion_envio_repository.crear_si_no_existe(db, Mensaje(
        evento="VERIFICACION_NUMERO", canal=canal,
        destinatario=Destinatario("mecanico", destino, mecanico.nombre),
        cuerpo=f"Hola {mecanico.nombre}, tu código de verificación para GeoTrack Auxilio Mecánico es: "
               f"{codigo}. Expira en 15 minutos.",
        clave_idempotencia=f"VERIFICACION_MECANICO:{mecanico.id}:{codigo}", prioridad=Prioridad.URGENTE,
    ))
    db.commit()
    return {"mensaje": "Código enviado al mecánico"}


def verificar_mecanico(db: Session, mecanico_id: int, codigo: str) -> dict:
    """Marca el numero como verificado si el codigo coincide y no vencio. Recibe id y codigo."""
    mecanico = _mecanico(db, mecanico_id)
    esperado = mecanico.codigo_verificacion or ""
    if not esperado or not hmac.compare_digest(esperado, (codigo or "").strip()):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Código de verificación incorrecto")
    if mecanico.codigo_expira_en and datetime.utcnow() > mecanico.codigo_expira_en:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El código de verificación ha expirado")
    mecanico.telefono_verificado = True
    mecanico.codigo_verificacion = mecanico.codigo_expira_en = None
    db.commit()
    return {"mensaje": "Número de teléfono verificado exitosamente"}


def _contactados(db: Session, codigo_incidencia: str) -> set:
    """Ids de mecanicos a los que ya se envio este auxilio. Recibe el codigo de la incidencia."""
    ids = set()
    for clave in repo.claves_con_prefijo(db, f"AYUDA_ASIGNADA:{codigo_incidencia}:"):
        parte = clave.rsplit(":", 1)[-1]
        if parte.isdigit():
            ids.add(int(parte))
    return ids


def proponer_mecanico(db: Session, incidencia_id: int, tipo: Optional[str]) -> dict:
    """El mecanico verificado mas cercano a la averia; si ya se contacto a alguno, el siguiente.
    Recibe la incidencia y el tipo de servicio opcional."""
    inc = incidencia_repository.obtener(db, incidencia_id)
    if inc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Incidencia no encontrada")
    todos = repo.mecanicos_verificados(db, tipo)
    if not todos:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No hay mecánicos verificados para este servicio")
    contactados = _contactados(db, inc.codigo)
    pool = [m for m in todos if m.id not in contactados] or todos

    def distancia(m):
        """Km de la averia al taller (999 si falta la ubicacion). Recibe el mecanico."""
        if None in (inc.latitud, inc.longitud, m.latitud, m.longitud):
            return 999.0
        return round(calcular_distancia(inc.latitud, inc.longitud, m.latitud, m.longitud), 2)

    mejor = min(pool, key=distancia)
    km = distancia(mejor)
    return {
        "mecanico_id": mejor.id, "nombre": mejor.nombre, "empresa_taller": mejor.empresa_taller,
        "telefono": mejor.telefono_whatsapp, "tipo_servicio": mejor.tipo_servicio,
        "distancia_km": km if km < 999 else None, "es_siguiente": bool(contactados),
        "ya_contactado": mejor.id in contactados,
    }


def asignar_mecanico(db: Session, incidencia_id: int, mecanico_id: int) -> dict:
    """Envia el auxilio al mecanico que confirmo el administrador. Recibe la incidencia y el mecanico."""
    if not settings.NOTIFICACIONES_HABILITADAS:
        raise HTTPException(status.HTTP_409_CONFLICT, "El centro de notificaciones está apagado")
    inc = incidencia_repository.obtener(db, incidencia_id)
    if inc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Incidencia no encontrada")
    if inc.estado != "ABIERTA":
        raise HTTPException(status.HTTP_409_CONFLICT, "La incidencia ya está resuelta")
    mecanico = _mecanico(db, mecanico_id)
    if not (mecanico.activo and mecanico.telefono_verificado):
        raise HTTPException(status.HTTP_409_CONFLICT, "El mecánico no está activo o no verificó su número")
    if not mecanico.telegram_chat_id:
        raise HTTPException(status.HTTP_409_CONFLICT, "El mecánico no tiene Telegram vinculado")
    if mecanico.id in _contactados(db, inc.codigo):
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya se le envió este auxilio a ese mecánico")
    perfil = conductor_repository.obtener_perfil(db, inc.conductor_id)
    avisos = operador.registrar(db, "AYUDA_ASIGNADA", {
        "incidencia": inc, "mecanico_id": mecanico.id, "mecanico_nombre": mecanico.nombre,
        "mecanico_chat_id": mecanico.telegram_chat_id,
        "conductor_nombre": perfil.nombre if perfil else "Conductor",
        "conductor_telefono": (perfil.telefono if perfil else "") or "",
    })
    return {"mensaje": f"Auxilio enviado a {mecanico.nombre}", "avisos": avisos}


# --- Plantillas ---

def listar_plantillas(db: Session) -> list:
    """Plantillas configuradas; agrega las de fabrica que falten. Sin input extra."""
    existentes = {(p.evento, p.canal) for p in repo.listar_plantillas(db)}
    faltantes = [(e, c, a, t) for e, c, a, t in EVENTOS_DEFAULT if (e, c) not in existentes]
    for evento, canal, asunto, cuerpo in faltantes:
        repo.guardar(db, NotificacionPlantilla(evento=evento, canal=canal, asunto=asunto, cuerpo=cuerpo, activo=True))
    if faltantes:
        db.commit()
    return repo.listar_plantillas(db)


def actualizar_plantilla(db: Session, plantilla_id: int, datos) -> NotificacionPlantilla:
    """Cambia el texto o apaga una plantilla (un aviso apagado no se envia). Recibe id y datos."""
    plantilla = repo.obtener_plantilla(db, plantilla_id)
    if plantilla is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Plantilla no encontrada")
    if not (datos.cuerpo or "").strip():
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "El texto del mensaje no puede quedar vacío")
    plantilla.cuerpo, plantilla.asunto, plantilla.activo = datos.cuerpo.strip(), datos.asunto, datos.activo
    db.commit()
    db.refresh(plantilla)
    return plantilla


# --- Conductores en Telegram ---

def conductores_vinculados(db: Session) -> dict:
    """Ids de conductores con Telegram vinculado. Sin input extra."""
    return {"conductores": [c.entidad_id for c in repo.contactos_activos(db, "conductor", "telegram")]}


def enlace_conductor(db: Session, conductor_id: int) -> dict:
    """Enlace firmado para que el conductor vincule su Telegram. Recibe el id del usuario conductor."""
    usuario = usuario_repository.obtener_por_id(db, conductor_id)
    if usuario is None or getattr(usuario, "rol", None) != "conductor":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conductor no encontrado")
    url = vinculos.enlace_telegram("conductor", conductor_id)
    if url is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Telegram no está configurado (bot y notificaciones)")
    return {"url": url}
