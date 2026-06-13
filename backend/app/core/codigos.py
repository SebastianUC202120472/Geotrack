# app/core/codigos.py
# Genera los códigos legibles tipo 'PD-001', 'RT-001'.

# Prefijos por tabla (qué letras lleva cada código).
PREFIJO_CLIENTE = "CL"
PREFIJO_PEDIDO = "PD"
PREFIJO_RUTA = "RT"
PREFIJO_DETALLE = "RD"
PREFIJO_HISTORIAL = "HP"
PREFIJO_VEHICULO = "VE"
# Usuarios: el prefijo depende del ROL (se distinguen a simple vista).
PREFIJO_ADMIN = "AD"
PREFIJO_CONDUCTOR = "CO"


def generar_codigo(prefijo: str, numero: int) -> str:
    """Construye el código legible: ('PD', 1) -> 'PD-001'."""
    return f"{prefijo}-{numero:03d}"


def asignar_codigo(db, obj, prefijo: str) -> str:
    """
    Asigna obj.codigo = 'PREFIJO-NNN' usando el id del registro.
    Hace flush si el id aún no existe (para obtenerlo sin cerrar la transacción).
    """
    if getattr(obj, "id", None) is None:
        db.flush()
    obj.codigo = generar_codigo(prefijo, obj.id)
    return obj.codigo


def prefijo_por_rol(rol: str) -> str:
    """Devuelve el prefijo de usuario según su rol: admin->AD, conductor->CO."""
    return PREFIJO_ADMIN if rol == "admin" else PREFIJO_CONDUCTOR
