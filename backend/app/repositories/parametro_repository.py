# app/repositories/parametro_repository.py
# Única capa que escribe/lee la tabla 'parametros_sistema' (CUS-06).
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.parametro import ParametroSistema


def listar_por_categoria(db: Session, categoria: str) -> List[ParametroSistema]:
    """Lista los parámetros de una categoría (ej. 'motivo_rechazo'), por id. Recibe: la categoría."""
    return (
        db.query(ParametroSistema)
        .filter(ParametroSistema.categoria == categoria)
        .order_by(ParametroSistema.id.asc())
        .all()
    )


def existe(db: Session, categoria: str, clave: str) -> bool:
    """True si ya existe un parámetro con esa categoría+clave (evita duplicados)."""
    return (
        db.query(ParametroSistema)
        .filter(ParametroSistema.categoria == categoria, ParametroSistema.clave == clave)
        .first()
        is not None
    )


def crear(db: Session, categoria: str, clave: str) -> ParametroSistema:
    """Crea un parámetro en una categoría. Recibe: categoría y clave (texto)."""
    parametro = ParametroSistema(categoria=categoria, clave=clave)
    db.add(parametro)
    db.commit()
    db.refresh(parametro)
    return parametro


def obtener_por_id(db: Session, parametro_id: int) -> Optional[ParametroSistema]:
    """Busca un parámetro por su id (para eliminarlo)."""
    return db.query(ParametroSistema).filter(ParametroSistema.id == parametro_id).first()


def eliminar(db: Session, parametro: ParametroSistema) -> None:
    """Borra un parámetro del catálogo (borrado físico: son datos de configuración)."""
    db.delete(parametro)
    db.commit()


def crear_con_valor(db: Session, categoria: str, clave: str, valor) -> ParametroSistema:
    """Crea un parámetro con valor_json (config numérica/estructurada). Recibe: categoría,
    clave y el valor a guardar en valor_json."""
    parametro = ParametroSistema(categoria=categoria, clave=clave, valor_json=valor)
    db.add(parametro)
    db.commit()
    db.refresh(parametro)
    return parametro


def fijar_valor(db: Session, categoria: str, clave: str, valor) -> ParametroSistema:
    """Crea o actualiza el valor_json de un parámetro (categoria+clave únicos). Recibe:
    categoría, clave y el nuevo valor."""
    fila = (
        db.query(ParametroSistema)
        .filter(ParametroSistema.categoria == categoria, ParametroSistema.clave == clave)
        .first()
    )
    if fila is None:
        return crear_con_valor(db, categoria, clave, valor)
    fila.valor_json = valor
    db.commit()
    db.refresh(fila)
    return fila
