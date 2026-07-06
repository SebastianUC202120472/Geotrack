# Mapeo del pipeline interno al vocabulario del portal + derivados de progreso.
# Logica pura (sin BD) para poder testearla sin conexion.

# Traduccion estado interno -> estado del portal. Cualquier estado no listado
# cae a POR_SALIR (nunca se expone un estado interno inesperado al publico).
_MAPA = {
    "EN_RUTA": "EN_RUTA",
    "ENTREGADO": "ENTREGADO",
    "OBSERVADO": "OBSERVADO",
    "FALLIDO": "REPROGRAMADO",
    "CANCELADO": "CANCELADO",
    "POR_RECOGER": "POR_SALIR",
    "LISTO_PARA_ENVIO": "POR_SALIR",
    "ASIGNADO": "POR_SALIR",
    "GEOCODIFICACION_FALLIDA": "POR_SALIR",
}


def mapear_estado(estado_pipeline: str) -> str:
    """Traduce un estado del pipeline al vocabulario del portal. Recibe el estado interno."""
    return _MAPA.get((estado_pipeline or "").upper(), "POR_SALIR")


def progreso(estado_portal: str, secuencia: int | None, total: int | None) -> dict:
    """Calcula pct/van (0-100%) y el paso 0-3 de la barra segun estado y posicion en ruta.
    Recibe el estado del portal, la secuencia de parada y el total de paradas (ambos opcionales)."""
    if estado_portal == "ENTREGADO":
        return {"pct": "100%", "van": "100%", "paso": 3}
    if estado_portal == "EN_RUTA":
        # avance real por posicion en la ruta si se conoce; si no, 50% de referencia.
        # (is not None: secuencia 0 es un valor valido, no debe caer al fallback)
        if secuencia is not None and total:
            frac = max(0, min(1, secuencia / total))
            v = str(round(frac * 100)) + "%"
            return {"pct": v, "van": v, "paso": 2}
        return {"pct": "50%", "van": "50%", "paso": 2}
    if estado_portal == "REPROGRAMADO":
        return {"pct": "48%", "van": "0%", "paso": 2}
    if estado_portal == "OBSERVADO":
        return {"pct": "35%", "van": "0%", "paso": 1}
    if estado_portal == "CANCELADO":
        return {"pct": "0%", "van": "0%", "paso": 0}
    # POR_SALIR
    return {"pct": "20%", "van": "0%", "paso": 1}
