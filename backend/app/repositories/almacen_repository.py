# app/repositories/almacen_repository.py
# Acceso a datos del módulo de almacén: trama (paquetes_esperados) y desconocidos.
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.paquete_esperado import PaqueteEsperado, EscaneoDesconocido


def agregar_esperados(db: Session, recojo_id: int, codigos: List[str]) -> Tuple[int, int]:
    """Crea filas ESPERADO para los códigos NUEVOS del recojo (dedup contra los ya existentes).
    Recibe: id de recojo y lista de códigos. Devuelve: (importados, duplicados)."""
    existentes = {p.codigo for p in db.query(PaqueteEsperado).filter(PaqueteEsperado.recojo_id == recojo_id).all()}
    importados = 0
    duplicados = 0
    for c in codigos:
        if c in existentes:
            duplicados += 1
            continue
        db.add(PaqueteEsperado(codigo=c, recojo_id=recojo_id, estado="ESPERADO"))
        existentes.add(c)
        importados += 1
    return importados, duplicados


def obtener_esperado(db: Session, recojo_id: int, codigo: str) -> Optional[PaqueteEsperado]:
    """Busca un código dentro de la trama de un recojo."""
    return (
        db.query(PaqueteEsperado)
        .filter(PaqueteEsperado.recojo_id == recojo_id, PaqueteEsperado.codigo == codigo)
        .first()
    )


def listar_esperados(db: Session, recojo_id: int) -> List[PaqueteEsperado]:
    """Trama completa de un recojo, ordenada por código."""
    return (
        db.query(PaqueteEsperado)
        .filter(PaqueteEsperado.recojo_id == recojo_id)
        .order_by(PaqueteEsperado.codigo.asc())
        .all()
    )


def contar(db: Session, recojo_id: int) -> Tuple[int, int, int]:
    """Devuelve (esperados, ingresados, desconocidos) de un recojo."""
    esperados = db.query(PaqueteEsperado).filter(PaqueteEsperado.recojo_id == recojo_id).count()
    ingresados = (
        db.query(PaqueteEsperado)
        .filter(PaqueteEsperado.recojo_id == recojo_id, PaqueteEsperado.estado == "INGRESADO")
        .count()
    )
    desconocidos = db.query(EscaneoDesconocido).filter(EscaneoDesconocido.recojo_id == recojo_id).count()
    return esperados, ingresados, desconocidos


def obtener_desconocido(db: Session, recojo_id: int, codigo: str) -> Optional[EscaneoDesconocido]:
    """Busca un desconocido ya registrado (para no duplicarlo)."""
    return (
        db.query(EscaneoDesconocido)
        .filter(EscaneoDesconocido.recojo_id == recojo_id, EscaneoDesconocido.codigo == codigo)
        .first()
    )


def agregar_desconocido(db: Session, recojo_id: int, codigo: str, usuario_id: int | None) -> EscaneoDesconocido:
    """Registra un código escaneado que no estaba en la trama. No hace commit."""
    desconocido = EscaneoDesconocido(recojo_id=recojo_id, codigo=codigo, escaneado_por=usuario_id)
    db.add(desconocido)
    return desconocido


def listar_desconocidos(db: Session, recojo_id: int) -> List[EscaneoDesconocido]:
    """Desconocidos de un recojo, ordenados por código."""
    return (
        db.query(EscaneoDesconocido)
        .filter(EscaneoDesconocido.recojo_id == recojo_id)
        .order_by(EscaneoDesconocido.codigo.asc())
        .all()
    )


def guardar_cambios(db: Session) -> None:
    """Confirma los cambios pendientes en PostgreSQL."""
    db.commit()
