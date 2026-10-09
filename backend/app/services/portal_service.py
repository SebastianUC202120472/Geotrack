from datetime import timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core import fechas
from app.repositories import portal_repository as repo
from app.services import estado_portal, enmascarado

# Etiquetas amables por estado destino de cada transicion del historial.
_ETIQUETAS = {
    "POR_RECOGER": ("Pedido recibido por SAVA", ""),
    "LISTO_PARA_ENVIO": ("Verificado en el centro SAVA", "empaque conforme"),
    "ASIGNADO": ("Programado para reparto", ""),
    "EN_RUTA": ("En camino a su direccion", ""),
    "ENTREGADO": ("Entregado", "evidencia registrada"),
    "FALLIDO": ("Intento de entrega sin exito", "se dejo constancia de visita"),
    "OBSERVADO": ("Incidencia registrada", "en gestion por el equipo SAVA"),
    "CANCELADO": ("Pedido cancelado", ""),
    "GEOCODIFICACION_FALLIDA": ("Verificando direccion de entrega", ""),
}

# Etiqueta para estados no catalogados: NUNCA se expone el estado interno crudo
# (estos textos salen por endpoints publicos).
_ETIQUETA_GENERICA = ("Actualizacion del envio", "")


def hora_local(momento) -> str:
    """Formatea una marca UTC naive como hora HH:MM de la zona de la operacion.
    Recibe el datetime (puede ser None). Las marcas se guardan en UTC, pero el texto
    lo lee el cliente final: sin convertir, una entrega de las 10:00 de Lima se le
    mostraria como las 15:00."""
    if momento is None:
        return ""
    if momento.tzinfo is None:
        momento = momento.replace(tzinfo=timezone.utc)
    return momento.astimezone(fechas.zona()).strftime("%H:%M")


def traducir_eventos(historial) -> list:
    """Convierte el historial de un pedido en eventos amables para el portal. Recibe la lista de historial.
    Marca ok/alerta/vivo segun el estado destino de cada transicion."""
    eventos = []
    ultimo = len(historial) - 1
    for i, h in enumerate(historial):
        t, d = _ETIQUETAS.get((h.estado_nuevo or "").upper(), _ETIQUETA_GENERICA)
        ev = {"t": t, "d": d, "h": hora_local(h.fecha_utc)}
        est = (h.estado_nuevo or "").upper()
        if est == "ENTREGADO":
            ev["ok"] = True
        elif est == "FALLIDO":
            ev["alerta"] = True
        elif i == ultimo and est == "EN_RUTA":
            ev["vivo"] = True
        eventos.append(ev)
    return eventos


def buscar_resumen(db: Session, codigo: str) -> dict:
    """Resumen ENMASCARADO de un pedido (pre-verificacion). Recibe el codigo. 404 si no existe."""
    p = repo.pedido_por_codigo(db, codigo)
    if not p:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return {
        "existe": True,
        "retail": p.cliente_origen,
        "destinoMask": enmascarado.mask_direccion(p.direccion_destino or ""),
        "telMask": enmascarado.mask_telefono(p.telefono_destinatario or ""),
        "estado": estado_portal.mapear_estado(p.estado),
        "tieneDni": bool(p.dni_destinatario),
    }


def detalle_pedido(db: Session, codigo: str) -> dict:
    """Detalle COMPLETO de un pedido (post-verificacion). Recibe el codigo. 404 si no existe."""
    p = repo.pedido_por_codigo(db, codigo)
    if not p:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    est = estado_portal.mapear_estado(p.estado)
    ruta, detalle, total = repo.ruta_y_detalle_de(db, p.id)
    secuencia = detalle.secuencia if detalle else None
    prog = estado_portal.progreso(est, secuencia, total)

    conductor_nombre, placa, parada = None, None, None
    if est == "EN_RUTA" and ruta:
        # Nombre publico del conductor: primero el del perfil (dato real de RR.HH.),
        # luego el del usuario. NUNCA se cae al correo: es un dato interno y este
        # texto se le muestra al cliente final en el portal.
        conductor_nombre = _nombre_publico_conductor(
            repo.perfil_conductor(db, ruta.conductor_id),
            repo.conductor_de_ruta(db, ruta.conductor_id),
        )
        placa = ruta.vehiculo_placa
        if secuencia is not None and total:
            parada = f"va en la parada {secuencia} de {total}"

    eventos = traducir_eventos(repo.historial_de(db, p.id))
    pod = repo.evidencia_de(db, p.id)

    data = {
        "retail": p.cliente_origen,
        "destino": p.direccion_destino,
        "estado": est,
        "etaT": _eta_titulo(est),
        "eta": "",
        "conductor": conductor_nombre,
        "placa": placa,
        "parada": parada,
        "pct": prog["pct"],
        "van": prog["van"],
        "nota": _nota(est),
        "podDisponible": bool(pod and (pod.url_foto)),
        "eventos": eventos,
    }
    if est == "ENTREGADO":
        data["recibido"] = _texto_recibido(p)
    if est == "REPROGRAMADO":
        data["motivo"] = detalle.motivo_fallo if detalle and detalle.motivo_fallo else "No se pudo entregar en el intento anterior"
    return data


def _nombre_publico_conductor(perfil, usuario) -> str:
    """Nombre del conductor apto para mostrar al cliente. Recibe el perfil y el usuario (ambos opcionales).
    Prefiere el nombre del perfil; si no hay ninguno devuelve una etiqueta generica. El correo
    es un dato interno y no debe salir nunca por un endpoint del portal."""
    for origen in (perfil, usuario):
        nombre = (getattr(origen, "nombre", None) or "").strip() if origen else ""
        if nombre:
            return nombre
    return "Conductor SAVA"


def _eta_titulo(est: str) -> str:
    """Titulo de ETA segun estado. Recibe el estado del portal."""
    return {
        "EN_RUTA": "Llega hoy", "ENTREGADO": "Entregado", "REPROGRAMADO": "Necesita nueva fecha",
        "POR_SALIR": "Por salir", "OBSERVADO": "En gestion", "CANCELADO": "Cancelado",
    }.get(est, "En proceso")


def _nota(est: str) -> str:
    """Nota descriptiva segun estado. Recibe el estado del portal."""
    return {
        "EN_RUTA": "Su pedido va en camino. La posicion se actualiza desde GeoTrack.",
        "ENTREGADO": "Ruta completada — su paquete fue entregado con evidencia.",
        "REPROGRAMADO": "El paquete esta seguro en el centro SAVA, listo para volver a salir en la fecha que elija.",
        "POR_SALIR": "Su pedido esta preparado y saldra a reparto en el proximo bloque.",
        "OBSERVADO": "Su pedido tiene una incidencia en gestion por el equipo SAVA.",
        "CANCELADO": "Este pedido fue cancelado. Contacte a su tienda para mas informacion.",
    }.get(est, "")


def _texto_recibido(p) -> str:
    """Texto de 'recibido por' para entregas. Recibe el pedido."""
    nombre = p.nombre_destinatario or "el destinatario"
    return f"Recibido por {nombre}."


def _estado_visible(p, det) -> str:
    """Estado del portal de un pedido. Recibe el pedido y su detalle de ruta de entrega (o None).
    estado_entrega del detalle solo es terminal (ENTREGADO/FALLIDO) o PENDIENTE; para el estado
    en curso (EN_RUTA, etc.) se usa el del pedido. Si se usara el detalle en curso, un EN_RUTA
    se mostraria como POR_SALIR (bug corregido)."""
    base = det.estado_entrega if (det and det.estado_entrega in ("ENTREGADO", "FALLIDO")) else p.estado
    return estado_portal.mapear_estado(base)


def _momento_local(momento, dia) -> str:
    """Hora local de un evento; si no es del dia consultado antepone la fecha (dd/mm). Recibe el datetime UTC y el dia."""
    if momento is None:
        return ""
    if fechas.fecha_local_de(momento) == dia:
        return hora_local(momento)
    m = momento.replace(tzinfo=timezone.utc).astimezone(fechas.zona())
    return m.strftime("%d/%m %H:%M")


def _eventos_empresa(historial, dia) -> list:
    """Linea de tiempo REAL de un pedido para el panel corporativo. Recibe su historial y el dia consultado."""
    eventos = []
    for h in historial:
        est = (h.estado_nuevo or "").upper()
        titulo, _ = _ETIQUETAS.get(est, _ETIQUETA_GENERICA)
        eventos.append({
            "h": _momento_local(h.fecha_utc, dia), "t": titulo,
            "ok": est == "ENTREGADO", "alerta": est in ("FALLIDO", "OBSERVADO", "CANCELADO"),
        })
    return eventos


def filas_empresa(db: Session, cliente_id: int, dia=None) -> list:
    """Pedidos de un cliente en una fecha (C45-01) con su estado visible y linea de tiempo real.
    Recibe el id del cliente y la fecha local (por defecto hoy). Devuelve una lista de filas."""
    dia = dia or fechas.hoy_local()
    pares = repo.pedidos_de_cliente_en_fecha(db, cliente_id, dia)
    historiales = repo.historial_de_pedidos(db, [p.id for p, _ in pares])
    filas = []
    for p, det in pares:
        est = _estado_visible(p, det)
        hora = (_momento_local(p.fecha_entrega, dia) if est == "ENTREGADO" else "") or "—"
        extra = ""
        if est == "EN_RUTA" and det:
            extra = f"Parada {det.secuencia}"
        elif est == "POR_SALIR":
            extra = "Sale en el proximo bloque"
        elif est == "OBSERVADO":
            extra = "En gestion"
        elif est == "REPROGRAMADO":
            extra = (det.motivo_fallo if det and det.motivo_fallo else "Intento sin éxito")
        filas.append({
            "cod": p.codigo, "ref": p.referencia_externa or "", "cliente": p.nombre_destinatario or "—",
            "dir": p.direccion_destino or "", "dist": p.distrito or "—",
            "estado": est, "h": hora, "extra": extra,
            "eventos": _eventos_empresa(historiales.get(p.id, []), dia),
        })
    return filas


def tabla_empresa(db: Session, cliente_id: int, dia=None) -> dict:
    """Filas + contadores de los pedidos de un cliente en una fecha. Recibe el id del cliente y la fecha (por defecto hoy)."""
    dia = dia or fechas.hoy_local()
    filas = filas_empresa(db, cliente_id, dia)
    contadores = {}
    for f in filas:
        contadores[f["estado"]] = contadores.get(f["estado"], 0) + 1
    return {"fecha": dia.isoformat(), "esHoy": dia == fechas.hoy_local(), "filas": filas, "contadores": contadores}


_ESTADO_LEGIBLE = {
    "ENTREGADO": "Entregado", "EN_RUTA": "En ruta", "POR_SALIR": "Por salir",
    "OBSERVADO": "Observado", "REPROGRAMADO": "Reprogramado", "CANCELADO": "Cancelado",
}


def excel_empresa(db: Session, cliente, dia=None) -> tuple[bytes, str]:
    """Exporta a Excel los pedidos de un cliente en una fecha (C45-02). Recibe el cliente y la fecha.
    Devuelve (bytes del .xlsx, nombre del archivo)."""
    import io
    from openpyxl import Workbook
    from openpyxl.styles import Font

    dia = dia or fechas.hoy_local()
    filas = filas_empresa(db, cliente.id, dia)
    wb = Workbook()
    hoja = wb.active
    hoja.title = "Pedidos"
    hoja.append([f"Pedidos de {cliente.razon_social} · {dia.strftime('%d/%m/%Y')}"])
    hoja["A1"].font = Font(bold=True, size=13)
    hoja.append([f"Generado desde el portal de clientes SAVA · {len(filas)} pedidos"])
    hoja.append([])
    columnas = ["Código SAVA", "Referencia", "Destinatario", "Dirección", "Distrito", "Estado", "Hora de entrega", "Detalle"]
    hoja.append(columnas)
    for celda in hoja[4]:
        celda.font = Font(bold=True)
    for f in filas:
        hoja.append([
            f["cod"], f["ref"], f["cliente"], f["dir"], f["dist"],
            _ESTADO_LEGIBLE.get(f["estado"], f["estado"]), "" if f["h"] == "—" else f["h"], f["extra"],
        ])
    for letra, ancho in zip("ABCDEFGH", (14, 16, 26, 42, 18, 14, 16, 30)):
        hoja.column_dimensions[letra].width = ancho

    buffer = io.BytesIO()
    wb.save(buffer)
    codigo = (cliente.codigo_acceso or str(cliente.id)).replace("/", "-")
    return buffer.getvalue(), f"pedidos_{codigo}_{dia.isoformat()}.xlsx"


def registrar_reprogramacion(db: Session, codigo: str, franja: str) -> dict:
    """Registra la franja pedida por el cliente + notifica al admin. Recibe codigo y franja.
    No cambia el pipeline (la reprogramacion real la decide el admin)."""
    from app.services import notificaciones_service
    p = repo.pedido_por_codigo(db, codigo)
    if not p:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    try:
        notificaciones_service.registrar(
            db, "reportes", "Reprogramacion solicitada por el cliente",
            f"Pedido {codigo}: el cliente pide la franja «{franja}»", "/reportes?pendientes=1", p.id)
    except Exception:
        pass
    db.commit()
    return {"ok": True}


# Cache en memoria de las estadisticas publicas (TTL corto): el landing hace polling
# cada 15 s por visitante, y sin cache cada visita escanearia la tabla de pedidos.
# Con el cache, la BD recibe como maximo unas pocas consultas por minuto sin importar
# cuantos visitantes tenga el landing.
_CACHE_ESTATS = {"hasta": 0.0, "datos": None}
_CACHE_ESTATS_TTL_SEG = 15


def estadisticas_publicas(db: Session, _reloj=None) -> dict:
    """Estadisticas agregadas + ultimo pedido ENMASCARADO para el landing (endpoint publico).
    Sin datos personales: solo conteos por estado, codigo enmascarado, retail corporativo
    y eventos genericos del historial (etiquetas + horas). Cachea el resultado unos
    segundos (anti-DoS del polling). Recibe db y un reloj opcional (tests)."""
    import time
    ahora = (_reloj or time.time)()
    if _CACHE_ESTATS["datos"] is not None and ahora < _CACHE_ESTATS["hasta"]:
        return _CACHE_ESTATS["datos"]
    datos = _calcular_estadisticas(db)
    _CACHE_ESTATS["datos"] = datos
    _CACHE_ESTATS["hasta"] = ahora + _CACHE_ESTATS_TTL_SEG
    return datos


def _calcular_estadisticas(db: Session) -> dict:
    """Calcula las estadisticas publicas contra la BD (sin cache). Recibe db."""
    # Reporte del dia operativo con actividad mas reciente. Se informa la fecha y si
    # corresponde a hoy: el landing no debe rotular como "de hoy" un dia anterior.
    dia, filas = repo.conteos_del_dia_reciente(db)
    conteos = {}
    for estado_pipeline, total in filas:
        est = estado_portal.mapear_estado(estado_pipeline)
        conteos[est] = conteos.get(est, 0) + total
    total = sum(conteos.values())
    entregados = conteos.get("ENTREGADO", 0)
    reporte = {
        "entregados": entregados,
        "enRuta": conteos.get("EN_RUTA", 0),
        "porSalir": conteos.get("POR_SALIR", 0),
        "incidencias": conteos.get("OBSERVADO", 0) + conteos.get("REPROGRAMADO", 0),
        "total": total,
        "pct": round(entregados / total * 100) if total else 0,
        "fecha": dia.isoformat() if dia else None,
        "esHoy": bool(dia and dia == fechas.hoy_local()),
    }

    # Tarjeta del pedido: el mas reciente, con codigo enmascarado y eventos genericos.
    p = repo.ultimo_pedido(db)
    pedido = None
    if p:
        pedido = {
            "codigo": enmascarado.mask_codigo(p.codigo or ""),
            "retail": p.cliente_origen,
            "estado": estado_portal.mapear_estado(p.estado),
            "eventos": traducir_eventos(repo.historial_de(db, p.id)),
        }
    return {"reporte": reporte, "pedido": pedido}


def respuesta_login_empresa(enviado: bool, otp: str, correo_mask: str, demo: bool) -> dict:
    """Arma la respuesta del login de empresa. Recibe si el correo salio, el OTP generado,
    el correo enmascarado y si el modo demostracion esta activo.
    Sin correo saliente el OTP no llega a nadie: o se devuelve en claro (solo en modo
    demostracion) o se avisa con un 503, en vez de responder "enviado" y dejar al
    usuario esperando un codigo que nunca va a recibir."""
    if enviado:
        return {"enviado": True, "correoMask": correo_mask}
    if demo:
        return {"enviado": False, "correoMask": correo_mask, "otpDemo": otp}
    raise HTTPException(
        status_code=503,
        detail="No se pudo enviar el codigo de verificacion. Contacte a SAVA para acceder al portal.",
    )


def ayuda_demo(db: Session, demo: bool) -> dict:
    """Credenciales y codigos de ejemplo para la sustentacion. Recibe db y si el modo
    demostracion esta activo.
    Con la bandera apagada devuelve {"activo": False} y NADA mas: estos datos incluyen
    claves en claro y no pueden salir por un endpoint publico en operacion normal."""
    if not demo:
        return {"activo": False}
    datos = repo.ayuda_demo(db)
    if not datos:
        return {"activo": False}
    empresas = datos.get("empresas") or []
    # Los pedidos se leen EN VIVO de las empresas de la ayuda (no de una lista guardada):
    # asi nunca muestra pedidos borrados y su estado avanza junto con la demostracion.
    ids = [c.id for c in (repo.cliente_por_codigo_acceso(db, e.get("codigo", "")) for e in empresas) if c]
    filas = [_fila_ayuda(p, det) for p, det in repo.pedidos_de_clientes(db, ids)]
    return {"activo": True, "empresas": empresas, "pedidos": seleccionar_pedidos_ayuda(filas)}


# Etiqueta corta de cada estado del portal para la ayuda de la demostracion.
ETIQUETAS_AYUDA = {
    "POR_SALIR": "Por salir", "EN_RUTA": "En camino", "ENTREGADO": "Entregado",
    "REPROGRAMADO": "Reprogramado", "OBSERVADO": "En gestión", "CANCELADO": "Cancelado",
}
MAX_PEDIDOS_AYUDA = 12


def _fila_ayuda(p, det) -> dict:
    """Fila de la ayuda: tienda, codigos, estado visible y ultimos 4 del DNI. Recibe pedido y detalle."""
    est = _estado_visible(p, det)
    return {
        "retail": p.cliente_origen or "",
        "codigo": p.codigo or "",
        "referencia": p.referencia_externa or "",
        "estado": ETIQUETAS_AYUDA.get(est, est.capitalize()),
        "dni": (p.dni_destinatario or "")[-4:] or "—",
    }


def seleccionar_pedidos_ayuda(filas: list, maximo: int = MAX_PEDIDOS_AYUDA) -> list:
    """Si caben, devuelve todos los pedidos; si son muchos, uno por tienda y estado (hasta el
    maximo). Recibe las filas ya armadas y el maximo a mostrar."""
    if len(filas) <= maximo:
        return filas
    vistos, salida = set(), []
    for f in filas:
        clave = (f["retail"], f["estado"])
        if clave not in vistos:
            vistos.add(clave)
            salida.append(f)
    return salida[:maximo]
