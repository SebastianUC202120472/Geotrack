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


def asegurar_motivos_iniciales(db: Session) -> None:
    """Siembra los motivos por defecto SOLO si el catálogo está vacío (al arrancar)."""
    if parametro_repository.listar_por_categoria(db, CATEGORIA_MOTIVO):
        return
    for texto in MOTIVOS_INICIALES:
        parametro_repository.crear(db, CATEGORIA_MOTIVO, texto)
