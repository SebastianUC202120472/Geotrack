# Genera los códigos legibles tipo 'PD-001', 'RT-001'.
PREFIJO_CLIENTE = "CL"
PREFIJO_PEDIDO = "PD"
PREFIJO_RUTA = "RT"
PREFIJO_DETALLE = "RD"
PREFIJO_HISTORIAL = "HP"
PREFIJO_VEHICULO = "VE"
PREFIJO_INCIDENCIA = "IN"
PREFIJO_RECOJO = "RC"
PREFIJO_ADMIN = "AD"
PREFIJO_ALMACEN = "AL"
PREFIJO_CONDUCTOR = "CO"

_PREFIJOS_POR_ROL = {
    "admin": PREFIJO_ADMIN,
    "almacen": PREFIJO_ALMACEN,
    "conductor": PREFIJO_CONDUCTOR,
}


def generar_codigo(prefijo: str, numero: int) -> str:
    """Construye el código legible: ('PD', 1) -> 'PD-001'."""
    return f"{prefijo}-{numero:03d}"


def asignar_codigo(db, obj, prefijo: str) -> str:
    """Asigna obj.codigo = 'PREFIJO-NNN'; hace flush si el id aún no existe."""
    if getattr(obj, "id", None) is None:
        db.flush()
    obj.codigo = generar_codigo(prefijo, obj.id)
    return obj.codigo


def prefijo_por_rol(rol: str) -> str:
    """Devuelve el prefijo según el rol (admin->AD, almacen->AL, conductor->CO); default CO."""
    return _PREFIJOS_POR_ROL.get(rol, PREFIJO_CONDUCTOR)
