from fastapi import HTTPException
from sqlalchemy.orm import Session

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
}


def traducir_eventos(historial) -> list:
    """Convierte el historial de un pedido en eventos amables para el portal. Recibe la lista de historial.
    Marca ok/alerta/vivo segun el estado destino de cada transicion."""
    eventos = []
    ultimo = len(historial) - 1
    for i, h in enumerate(historial):
        t, d = _ETIQUETAS.get((h.estado_nuevo or "").upper(), (h.estado_nuevo or "Actualizacion", ""))
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
        cond = repo.conductor_de_ruta(db, ruta.conductor_id)
        # Obtiene el nombre del conductor, fallando a correo si no hay nombre.
        conductor_nombre = (getattr(cond, "nombre", None) or getattr(cond, "correo", None)) if cond else None
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
