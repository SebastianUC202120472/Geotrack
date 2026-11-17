# Operaciones de la base de conocimiento que usan el arranque y la administracion: cargar la
# semilla, rearmar el indice de busqueda y validar lo que escribe un administrador.
from app.conocimiento.buscador import indice
from app.conocimiento.semilla import articulos_semilla
from app.core.config import settings
from app.db.database import SessionLocal, preparar_tablas
from app.repositories import conocimiento_repository
from app.services.defensa import intenta_cambiar_reglas, neutralizar_texto
from app.services.salida import _RE_MARKDOWN, _RE_URL, enlace_permitido


class ContenidoNoPermitido(ValueError):
    """El texto de un articulo trae instrucciones para el asistente o enlaces fuera de SAVA."""


def recargar_indice() -> int:
    """Rearma el indice de busqueda con los articulos activos de la base. Sin input; devuelve cuantos."""
    db = SessionLocal()
    try:
        articulos = [
            {"clave": a.clave, "idioma": a.idioma, "titulo": a.titulo, "contenido": a.contenido, "etiquetas": a.etiquetas}
            for a in conocimiento_repository.listar_activos(db)
        ]
    finally:
        db.close()
    indice.cargar(articulos)
    return len(articulos)


def preparar_conocimiento() -> tuple[int, int]:
    """Crea las tablas, carga la semilla si la base esta vacia y arma el indice. Sin input;
    devuelve (articulos cargados de la semilla, articulos activos)."""
    preparar_tablas()
    db = SessionLocal()
    try:
        cargados = conocimiento_repository.cargar_semilla(db, articulos_semilla())
    finally:
        db.close()
    return cargados, recargar_indice()


def validar_contenido(*textos: str) -> None:
    """Rechaza texto con ordenes para el asistente o enlaces a otros dominios (defensa en profundidad:
    en tiempo de respuesta igual se neutraliza). Recibe los textos del articulo."""
    for texto in textos:
        if not texto:
            continue
        if intenta_cambiar_reglas(texto) or neutralizar_texto(texto)[1]:
            raise ContenidoNoPermitido("El texto parece contener instrucciones para el asistente. Redáctalo como información.")
        urls = [m.group(2) for m in _RE_MARKDOWN.finditer(texto)] + [m.group(0) for m in _RE_URL.finditer(texto)]
        if any(not enlace_permitido(u, settings.dominios_permitidos) for u in urls):
            raise ContenidoNoPermitido("Solo se permiten enlaces a SAVA o rutas del sitio (por ejemplo /portal).")
