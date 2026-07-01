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


def asegurar_motivos_iniciales(db: Session) -> None:
    """Siembra los motivos por defecto SOLO si el catálogo está vacío (al arrancar)."""
    if parametro_repository.listar_por_categoria(db, CATEGORIA_MOTIVO):
        return
    for texto in MOTIVOS_INICIALES:
        parametro_repository.crear(db, CATEGORIA_MOTIVO, texto)
