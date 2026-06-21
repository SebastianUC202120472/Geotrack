# app/repositories/incidencia_repository.py
# Única capa que consulta/escribe en la tabla 'incidencias' (CUS-30).
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.incidencia import Incidencia
from app.core.codigos import asignar_codigo, PREFIJO_INCIDENCIA


def crear(db: Session, **datos) -> Incidencia:
    """Crea una incidencia y le asigna su código legible IN-001. Recibe: los campos."""
    incidencia = Incidencia(**datos)
    db.add(incidencia)
    asignar_codigo(db, incidencia, PREFIJO_INCIDENCIA)  # hace flush -> id
    db.commit()
    db.refresh(incidencia)
    return incidencia


def obtener_abierta_por_ruta(db: Session, ruta_id: int) -> Optional[Incidencia]:
    """Devuelve la incidencia ABIERTA de una ruta (o None). Recibe: id de ruta."""
    return (
        db.query(Incidencia)
        .filter(Incidencia.ruta_id == ruta_id, Incidencia.estado == "ABIERTA")
        .order_by(Incidencia.creado_en.desc())
        .first()
    )


def tiene_abierta(db: Session, ruta_id: int) -> bool:
    """True si la ruta tiene una incidencia ABIERTA (= está pausada). Recibe: id de ruta."""
    return obtener_abierta_por_ruta(db, ruta_id) is not None


def rutas_con_incidencia_abierta(db: Session) -> set:
    """Conjunto de ruta_id con alguna incidencia ABIERTA (para marcar el mapa de flota)."""
    filas = db.query(Incidencia.ruta_id).filter(Incidencia.estado == "ABIERTA").all()
    return {r[0] for r in filas}


def listar(db: Session, estado: Optional[str] = None) -> List[Incidencia]:
    """Lista las incidencias (abiertas primero, recientes arriba). Recibe: estado opcional."""
    consulta = db.query(Incidencia)
    if estado:
        consulta = consulta.filter(Incidencia.estado == estado)
    return consulta.order_by(Incidencia.estado.asc(), Incidencia.creado_en.desc()).all()


def obtener(db: Session, incidencia_id: int) -> Optional[Incidencia]:
    """Busca una incidencia por id."""
    return db.query(Incidencia).filter(Incidencia.id == incidencia_id).first()


def contar_abiertas(db: Session) -> int:
    """Cuenta las incidencias ABIERTAS (para el aviso/contador del panel)."""
    return db.query(Incidencia).filter(Incidencia.estado == "ABIERTA").count()


def guardar(db: Session) -> None:
    """Confirma los cambios pendientes."""
    db.commit()
