# app/services/parametro_service.py
# CUS-06: catálogo de parámetros administrables. Hoy, motivos de rechazo.
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories import parametro_repository

# Categoría de los motivos de rechazo dentro de parametros_sistema.
CATEGORIA_MOTIVO = "motivo_rechazo"

# Motivos por defecto (los que antes estaban fijos en la app móvil). Se siembran si
# el catálogo está vacío, para que el sistema tenga motivos desde el arranque.
MOTIVOS_INICIALES = [
    "Cliente ausente",
    "Dirección incorrecta",
    "Pedido rechazado",
    "Zona inaccesible",
    "Otro",
]


def listar_motivos(db: Session) -> list:
    """CUS-06: devuelve los motivos de rechazo del catálogo. Recibe: la sesión."""
    filas = parametro_repository.listar_por_categoria(db, CATEGORIA_MOTIVO)
    return [{"id": p.id, "texto": p.clave} for p in filas]


def crear_motivo(db: Session, texto: str) -> dict:
    """CUS-06: agrega un motivo de rechazo (rechaza duplicados). Recibe: el texto."""
    if parametro_repository.existe(db, CATEGORIA_MOTIVO, texto):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ese motivo ya existe")
    parametro = parametro_repository.crear(db, CATEGORIA_MOTIVO, texto)
    return {"id": parametro.id, "texto": parametro.clave}


def eliminar_motivo(db: Session, motivo_id: int) -> dict:
    """CUS-06: elimina un motivo de rechazo del catálogo. Recibe: su id."""
    parametro = parametro_repository.obtener_por_id(db, motivo_id)
    if parametro is None or parametro.categoria != CATEGORIA_MOTIVO:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Motivo no encontrado")
    parametro_repository.eliminar(db, parametro)
    return {"mensaje": "Motivo eliminado"}


# CUS-34: parámetros de combustible (categoría aparte). Cada uno es una fila cuyo
# 'clave' es el nombre del parámetro y 'valor_json' guarda el número.
CATEGORIA_COMBUSTIBLE = "combustible"
COMBUSTIBLE_DEFAULTS = {
    "consumo_l_100km": 12.0,    # litros por cada 100 km (rendimiento típico de un furgón)
    "precio_soles_litro": 16.5,  # S/ por litro
}


def asegurar_combustible_inicial(db: Session) -> None:
    """Siembra los parámetros de combustible por defecto si aún no existen (al arrancar)."""
    existentes = {p.clave for p in parametro_repository.listar_por_categoria(db, CATEGORIA_COMBUSTIBLE)}
    for clave, valor in COMBUSTIBLE_DEFAULTS.items():
        if clave not in existentes:
            parametro_repository.crear_con_valor(db, CATEGORIA_COMBUSTIBLE, clave, valor)


def obtener_combustible(db: Session) -> dict:
    """CUS-34: devuelve {consumo_l_100km, precio_soles_litro} como floats. Si falta o es
    inválido un valor, usa el default. Recibe: la sesión de BD."""
    filas = {p.clave: p.valor_json for p in parametro_repository.listar_por_categoria(db, CATEGORIA_COMBUSTIBLE)}
    resultado = {}
    for clave, default in COMBUSTIBLE_DEFAULTS.items():
        try:
            resultado[clave] = float(filas.get(clave, default))
        except (TypeError, ValueError):
            resultado[clave] = default
    return resultado


def actualizar_combustible(db: Session, consumo_l_100km: float, precio_soles_litro: float) -> dict:
    """CUS-34: guarda los dos parámetros de combustible (crea si no existen). Recibe:
    consumo (L/100km) y precio (S//L). Devuelve el dict resultante."""
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
