# Acceso a la base de conocimiento propia del modulo.
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.fechas import ahora_utc
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


def crear(db: Session, datos: dict, editado_por: str, confirmar: bool = False) -> ArticuloConocimiento:
    """Crea un articulo y su primera entrada de historial. Recibe los datos validados, quien lo crea y
    si se guarda ya (la semilla confirma todo junto al final)."""
    articulo = ArticuloConocimiento(**datos, editado_por=editado_por, version=1)
    db.add(articulo)
    db.flush()
    _registrar_historial(db, articulo, "CREADO")
    if confirmar:
        db.commit()
        db.refresh(articulo)
    return articulo


def cargar_semilla(db: Session, articulos: list[dict]) -> int:
    """Carga los articulos semilla solo si la base de conocimiento esta vacia. Recibe la lista; devuelve cuantos cargo."""
    if contar(db) > 0:
        return 0
    for datos in articulos:
        crear(db, datos, editado_por="semilla")
    db.commit()
    return len(articulos)


def listar(db: Session, idioma: str | None = None, texto: str | None = None) -> list[ArticuloConocimiento]:
    """Articulos para la administracion (activos e inactivos), filtrados por idioma y texto. Recibe ambos filtros."""
    consulta = select(ArticuloConocimiento)
    if idioma:
        consulta = consulta.where(ArticuloConocimiento.idioma == idioma)
    if texto:
        patron = f"%{texto.lower()}%"
        consulta = consulta.where(
            func.lower(ArticuloConocimiento.titulo).like(patron)
            | func.lower(ArticuloConocimiento.contenido).like(patron)
            | func.lower(ArticuloConocimiento.clave).like(patron)
        )
    return list(db.execute(consulta.order_by(ArticuloConocimiento.categoria, ArticuloConocimiento.clave,
                                             ArticuloConocimiento.idioma)).scalars().all())


def obtener(db: Session, articulo_id: int) -> ArticuloConocimiento | None:
    """Articulo por id. Recibe el id."""
    return db.get(ArticuloConocimiento, articulo_id)


def existe(db: Session, clave: str, idioma: str) -> bool:
    """Dice si ya hay un articulo con esa clave e idioma. Recibe clave e idioma."""
    return db.execute(select(ArticuloConocimiento.id).where(
        ArticuloConocimiento.clave == clave, ArticuloConocimiento.idioma == idioma)).first() is not None


def actualizar(db: Session, articulo: ArticuloConocimiento, datos: dict, editado_por: str, accion: str) -> ArticuloConocimiento:
    """Aplica cambios, sube la version y deja la copia en el historial. Recibe el articulo, los cambios,
    quien edita y la accion (EDITADO | ACTIVADO | DESACTIVADO)."""
    for campo, valor in datos.items():
        setattr(articulo, campo, valor)
    articulo.version += 1
    articulo.editado_por = editado_por
    articulo.editado_en = ahora_utc()
    _registrar_historial(db, articulo, accion)
    db.commit()
    db.refresh(articulo)
    return articulo


def historial(db: Session, articulo_id: int) -> list[HistorialArticulo]:
    """Versiones de un articulo, de la mas reciente a la mas antigua. Recibe el id."""
    return list(db.execute(select(HistorialArticulo).where(HistorialArticulo.articulo_id == articulo_id)
                           .order_by(HistorialArticulo.version.desc())).scalars().all())
