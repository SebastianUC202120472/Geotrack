from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories import parametro_repository

CATEGORIA_MOTIVO = "motivo_rechazo"

MOTIVOS_INICIALES = [
    "Cliente ausente",
    "Dirección incorrecta",
    "Pedido rechazado",
    "Zona inaccesible",
    "Otro",
]


def listar_motivos(db: Session) -> list:
    """Devuelve los motivos de rechazo del catálogo. Recibe: sesión de BD."""
    filas = parametro_repository.listar_por_categoria(db, CATEGORIA_MOTIVO)
    return [{"id": p.id, "texto": p.clave} for p in filas]


def crear_motivo(db: Session, texto: str) -> dict:
    """Agrega un motivo de rechazo; rechaza duplicados. Recibe: sesión y texto."""
    if parametro_repository.existe(db, CATEGORIA_MOTIVO, texto):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ese motivo ya existe")
    parametro = parametro_repository.crear(db, CATEGORIA_MOTIVO, texto)
    return {"id": parametro.id, "texto": parametro.clave}


def eliminar_motivo(db: Session, motivo_id: int) -> dict:
    """Elimina un motivo de rechazo del catálogo. Recibe: sesión e id del motivo."""
    parametro = parametro_repository.obtener_por_id(db, motivo_id)
    if parametro is None or parametro.categoria != CATEGORIA_MOTIVO:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Motivo no encontrado")
    parametro_repository.eliminar(db, parametro)
    return {"mensaje": "Motivo eliminado"}


CATEGORIA_COMBUSTIBLE = "combustible"
COMBUSTIBLE_DEFAULTS = {
    "consumo_l_100km": 12.0,
    "precio_soles_litro": 16.5,
}


def asegurar_combustible_inicial(db: Session) -> None:
    """Siembra los parámetros de combustible por defecto si aún no existen (al arrancar)."""
    existentes = {p.clave for p in parametro_repository.listar_por_categoria(db, CATEGORIA_COMBUSTIBLE)}
    for clave, valor in COMBUSTIBLE_DEFAULTS.items():
        if clave not in existentes:
            parametro_repository.crear_con_valor(db, CATEGORIA_COMBUSTIBLE, clave, valor)


def obtener_combustible(db: Session) -> dict:
    """Devuelve los parametros de combustible como floats; usa defaults si faltan. Recibe: sesión de BD."""
    filas = {p.clave: p.valor_json for p in parametro_repository.listar_por_categoria(db, CATEGORIA_COMBUSTIBLE)}
    resultado = {}
    for clave, default in COMBUSTIBLE_DEFAULTS.items():
        try:
            resultado[clave] = float(filas.get(clave, default))
        except (TypeError, ValueError):
            resultado[clave] = default
    return resultado


def actualizar_combustible(db: Session, consumo_l_100km: float, precio_soles_litro: float) -> dict:
    """Guarda consumo y precio de combustible; crea las filas si no existen. Recibe: sesión, consumo y precio."""
    if consumo_l_100km <= 0 or precio_soles_litro <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Los valores deben ser mayores a 0")
    parametro_repository.fijar_valor(db, CATEGORIA_COMBUSTIBLE, "consumo_l_100km", float(consumo_l_100km))
    parametro_repository.fijar_valor(db, CATEGORIA_COMBUSTIBLE, "precio_soles_litro", float(precio_soles_litro))
    return obtener_combustible(db)


CATEGORIA_CONTACTO = "contacto"
CLAVE_TELEFONO = "telefono_coordinacion"


def obtener_contacto(db: Session) -> dict:
    """Devuelve el telefono de coordinacion que ve el conductor en la app (o None). Recibe: sesión de BD."""
    filas = {p.clave: p.valor_json for p in parametro_repository.listar_por_categoria(db, CATEGORIA_CONTACTO)}
    telefono = filas.get(CLAVE_TELEFONO)
    return {"telefono_coordinacion": telefono if isinstance(telefono, str) and telefono else None}


def actualizar_contacto(db: Session, telefono: str | None) -> dict:
    """Guarda el telefono de coordinacion (vacio lo borra). Recibe: sesión y telefono ya validado."""
    parametro_repository.fijar_valor(db, CATEGORIA_CONTACTO, CLAVE_TELEFONO, telefono or None)
    return obtener_contacto(db)


CATEGORIA_PORTAL = "portal"
CLAVE_FRANJAS = "franjas_reprogramacion"
FRANJAS_DEFECTO = ["Mañana · 9 am – 1 pm", "Mañana · 2 pm – 6 pm", "Sábado · 9 am – 1 pm"]


def obtener_franjas(db: Session) -> list:
    """Franjas que el cliente puede elegir al reprogramar en el portal; las de fabrica si no hay. Recibe: sesión."""
    filas = {p.clave: p.valor_json for p in parametro_repository.listar_por_categoria(db, CATEGORIA_PORTAL)}
    franjas = filas.get(CLAVE_FRANJAS)
    if isinstance(franjas, list) and franjas and all(isinstance(f, str) for f in franjas):
        return franjas
    return list(FRANJAS_DEFECTO)


def actualizar_franjas(db: Session, franjas: list) -> list:
    """Guarda las franjas de reprogramacion (ya validadas). Recibe: sesión y la lista."""
    parametro_repository.fijar_valor(db, CATEGORIA_PORTAL, CLAVE_FRANJAS, list(franjas))
    return obtener_franjas(db)


def asegurar_motivos_iniciales(db: Session) -> None:
    """Siembra los motivos por defecto SOLO si el catálogo está vacío (al arrancar)."""
    if parametro_repository.listar_por_categoria(db, CATEGORIA_MOTIVO):
        return
    for texto in MOTIVOS_INICIALES:
        parametro_repository.crear(db, CATEGORIA_MOTIVO, texto)
