# Acceso a la base de conocimiento propia del modulo.
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.conocimiento import ArticuloConocimiento, HistorialArticulo


def listar_activos(db: Session) -> list[ArticuloConocimiento]:
    """Todos los articulos activos, en ambos idiomas. Sin input."""
    return list(db.execute(
        select(ArticuloConocimiento).where(ArticuloConocimiento.activo.is_(True)).order_by(ArticuloConocimiento.id)
    ).scalars().all())


def contar(db: Session) -> int:
    """Cantidad de articulos (activos o no). Sin input."""
    return int(db.execute(select(func.count(ArticuloConocimiento.id))).scalar() or 0)


def _registrar_historial(db: Session, articulo: ArticuloConocimiento, accion: str) -> None:
    """Agrega al historial la version actual del articulo. Recibe el articulo y la accion."""
    db.add(HistorialArticulo(
        articulo_id=articulo.id, version=articulo.version, accion=accion, titulo=articulo.titulo,
        contenido=articulo.contenido, etiquetas=articulo.etiquetas, activo=articulo.activo,
        editado_por=articulo.editado_por,
    ))


def crear(db: Session, datos: dict, editado_por: str) -> ArticuloConocimiento:
    """Crea un articulo y su primera entrada de historial. Recibe los datos validados y quien lo crea."""
    articulo = ArticuloConocimiento(**datos, editado_por=editado_por, version=1)
    db.add(articulo)
    db.flush()
    _registrar_historial(db, articulo, "CREADO")
    return articulo


def cargar_semilla(db: Session, articulos: list[dict]) -> int:
    """Carga los articulos semilla solo si la base de conocimiento esta vacia. Recibe la lista; devuelve cuantos cargo."""
    if contar(db) > 0:
        return 0
    for datos in articulos:
        crear(db, datos, editado_por="semilla")
    db.commit()
    return len(articulos)
