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


def traducir_eventos(historial) -> list:
    """Convierte el historial de un pedido en eventos amables para el portal. Recibe la lista de historial.
    Marca ok/alerta/vivo segun el estado destino de cada transicion."""
    eventos = []
    ultimo = len(historial) - 1
    for i, h in enumerate(historial):
        t, d = _ETIQUETAS.get((h.estado_nuevo or "").upper(), _ETIQUETA_GENERICA)
        ev = {"t": t, "d": d, "h": h.fecha_utc.strftime("%H:%M") if h.fecha_utc else ""}
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


def tabla_empresa(db: Session, cliente_id: int) -> dict:
    """Filas + contadores de los pedidos de hoy de un cliente. Recibe el id del cliente."""
    filas = []
    contadores = {}
    for p, det in repo.pedidos_de_cliente_hoy(db, cliente_id):
        # estado_entrega del detalle solo es terminal (ENTREGADO/FALLIDO) o PENDIENTE;
        # para el estado en curso (EN_RUTA, etc.) se usa el estado del pedido. Si se usara
        # el detalle en curso, un EN_RUTA se mostraria como POR_SALIR (bug corregido).
        base = det.estado_entrega if (det and det.estado_entrega in ("ENTREGADO", "FALLIDO")) else p.estado
        est = estado_portal.mapear_estado(base)
        hora = p.fecha_entrega.strftime("%H:%M") if (est == "ENTREGADO" and p.fecha_entrega) else "—"
        extra = ""
        if est == "EN_RUTA" and det:
            extra = f"Parada {det.secuencia}"
        elif est == "POR_SALIR":
            extra = "Sale en el proximo bloque"
        elif est == "OBSERVADO":
            extra = "En gestion"
        filas.append({
            "cod": p.codigo, "cliente": p.nombre_destinatario or "—",
            "dir": p.direccion_destino or "", "dist": p.distrito or "—",
            "estado": est, "h": hora, "extra": extra,
        })
        contadores[est] = contadores.get(est, 0) + 1
    return {"filas": filas, "contadores": contadores}


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
