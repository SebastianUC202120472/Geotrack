# app/core/codigos.py
# ============================================================================
# CAPA: CORE / UTILIDAD — Códigos legibles de negocio
# ----------------------------------------------------------------------------
# ¿QUÉ HACE?  Genera los códigos legibles tipo 'PD-001', 'RT-001'... que hacen
#             la base de datos entendible y TRAZABLE a simple vista.
# ¿CÓMO?      El 'id' entero (llave primaria interna) se mantiene para las
#             relaciones; este código es un campo APARTE, derivado del id.
#             Ej.: pedido con id=1 -> codigo 'PD-001'.
# ¿CON QUÉ SE CONECTA?
#   - Lo USAN: los repositorios, al crear cada registro (tras conocer su id).
# ============================================================================

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
