# Endpoints de la pantalla de administracion del panel (solo rol admin, con su token del panel).
#   - Base de conocimiento: listar, crear, editar, activar/desactivar, historial y probar busqueda.
#     Cada cambio sube la version, deja copia en el historial (quien y cuando) y rearma el indice.
#     Se rechaza el texto con instrucciones para el asistente o enlaces fuera de SAVA.
#   - Bandeja: conversaciones derivadas a una persona, con sus mensajes (ya enmascarados).
#   - Metricas: conversaciones, % resueltas sin persona, temas, empresas captadas, seguridad.
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.api.deps import obtener_admin, verificar_origen
from app.conocimiento.buscador import indice
from app.conocimiento.servicio import ContenidoNoPermitido, recargar_indice, validar_contenido
from app.core.config import settings
from app.core.registro import log
from app.db.database import get_db
from app.repositories import conocimiento_repository as kb
from app.repositories import conversacion_repository, gestion_repository, metricas_repository
from app.schemas.admin import (
    ArticuloDatos, ArticuloNuevo, ArticuloSalida, DerivacionDetalle, DerivacionSalida, EstadoArticulo, MensajeSalida,
    PruebaBusqueda, VersionSalida,
)

router = APIRouter()
_ESCRIBE = [Depends(verificar_origen)]   # las escrituras exigen ademas el origen del sitio


def _validar(datos: ArticuloDatos) -> None:
    """Rechaza contenido con instrucciones o enlaces externos (400). Recibe los datos del articulo."""
    try:
        validar_contenido(datos.titulo, datos.contenido, datos.etiquetas)
    except ContenidoNoPermitido as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))


def _articulo(db: Session, articulo_id: int):
    """Articulo por id o 404. Recibe db e id."""
    articulo = kb.obtener(db, articulo_id)
    if articulo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "El artículo no existe")
    return articulo


@router.get("/articulos", response_model=list[ArticuloSalida])
def listar_articulos(idioma: str | None = Query(None, pattern="^(es|en)$"), q: str | None = Query(None, max_length=100),
                     db: Session = Depends(get_db), admin: dict = Depends(obtener_admin)):
    """Articulos de la base de conocimiento (activos e inactivos). Recibe idioma y texto a buscar."""
    return kb.listar(db, idioma, (q or "").strip() or None)


@router.post("/articulos", response_model=ArticuloSalida, status_code=201, dependencies=_ESCRIBE)
async def crear_articulo(datos: ArticuloNuevo, db: Session = Depends(get_db), admin: dict = Depends(obtener_admin)):
    """Crea un articulo nuevo y rearma el indice. Recibe clave, idioma, categoria, titulo, contenido y etiquetas."""
    _validar(datos)
    if kb.existe(db, datos.clave, datos.idioma):
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe un artículo con esa clave en ese idioma")
    articulo = kb.crear(db, datos.model_dump(), admin["correo"], confirmar=True)
    await run_in_threadpool(recargar_indice)
    log.info("Artículo %s/%s creado por %s", articulo.clave, articulo.idioma, admin["id"])
    return articulo


@router.put("/articulos/{articulo_id}", response_model=ArticuloSalida, dependencies=_ESCRIBE)
async def editar_articulo(articulo_id: int, datos: ArticuloDatos, db: Session = Depends(get_db),
                          admin: dict = Depends(obtener_admin)):
    """Edita un articulo (nueva version en el historial) y rearma el indice. Recibe id y campos."""
    _validar(datos)
    articulo = kb.actualizar(db, _articulo(db, articulo_id), datos.model_dump(), admin["correo"], "EDITADO")
    await run_in_threadpool(recargar_indice)
    log.info("Artículo %s editado por %s (versión %s)", articulo.id, admin["id"], articulo.version)
    return articulo


@router.post("/articulos/{articulo_id}/estado", response_model=ArticuloSalida, dependencies=_ESCRIBE)
async def cambiar_estado(articulo_id: int, datos: EstadoArticulo, db: Session = Depends(get_db),
                         admin: dict = Depends(obtener_admin)):
    """Activa o desactiva un articulo (el asistente deja de usarlo al instante). Recibe id y {activo}."""
    articulo = _articulo(db, articulo_id)
    if articulo.activo != datos.activo:
        articulo = kb.actualizar(db, articulo, {"activo": datos.activo}, admin["correo"],
                                 "ACTIVADO" if datos.activo else "DESACTIVADO")
        await run_in_threadpool(recargar_indice)
    return articulo


@router.get("/articulos/{articulo_id}/historial", response_model=list[VersionSalida])
def historial_articulo(articulo_id: int, db: Session = Depends(get_db), admin: dict = Depends(obtener_admin)):
    """Versiones de un articulo con quien y cuando las hizo. Recibe el id."""
    _articulo(db, articulo_id)
    return kb.historial(db, articulo_id)


@router.post("/probar")
def probar_busqueda(datos: PruebaBusqueda, admin: dict = Depends(obtener_admin)):
    """Muestra que articulos recuperaria el asistente para una pregunta (sin llamar a la IA). Recibe consulta e idioma."""
    resultados = indice.buscar(datos.consulta, datos.idioma, settings.ATENCION_KB_RESULTADOS)
    return [{"clave": r.clave, "idioma": r.idioma, "titulo": r.titulo, "puntaje": r.puntaje,
             "se_usaria": r.puntaje >= settings.ATENCION_KB_PUNTAJE_MINIMO} for r in resultados]


@router.get("/derivaciones", response_model=list[DerivacionSalida])
def listar_derivaciones(estado: str | None = Query(None, pattern="^(PENDIENTE|ATENDIDA)$"),
                        db: Session = Depends(get_db), admin: dict = Depends(obtener_admin)):
    """Bandeja de conversaciones derivadas a una persona. Recibe el estado (opcional)."""
    return gestion_repository.listar_derivaciones(db, estado)


@router.get("/derivaciones/{derivacion_id}", response_model=DerivacionDetalle)
def detalle_derivacion(derivacion_id: int, db: Session = Depends(get_db), admin: dict = Depends(obtener_admin)):
    """Derivacion con los mensajes de su conversacion (enmascarados). Recibe el id."""
    derivacion = gestion_repository.obtener_derivacion(db, derivacion_id)
    if derivacion is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "La derivación no existe")
    conversacion = conversacion_repository.obtener(db, derivacion.conversacion_id)
    mensajes = conversacion_repository.ultimos_mensajes(db, derivacion.conversacion_id, 200)
    log.info("Derivación %s consultada por %s", derivacion_id, admin["id"])
    return DerivacionDetalle(
        **DerivacionSalida.model_validate(derivacion).model_dump(),
        pagina=conversacion.pagina if conversacion else "landing",
        mensajes=[MensajeSalida.model_validate(m) for m in mensajes],
    )


@router.post("/derivaciones/{derivacion_id}/atender", response_model=DerivacionSalida, dependencies=_ESCRIBE)
def atender_derivacion(derivacion_id: int, db: Session = Depends(get_db), admin: dict = Depends(obtener_admin)):
    """Marca la derivacion como atendida (queda quien y cuando). Recibe el id."""
    derivacion = gestion_repository.obtener_derivacion(db, derivacion_id)
    if derivacion is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "La derivación no existe")
    if derivacion.estado == "ATENDIDA":
        return derivacion
    return gestion_repository.atender_derivacion(db, derivacion, admin["correo"])


@router.get("/metricas")
def metricas(dias: int = Query(30, ge=1, le=90), db: Session = Depends(get_db), admin: dict = Depends(obtener_admin)):
    """Metricas del asistente de los ultimos dias. Recibe cuantos dias (1 a 90)."""
    titulos = {a.clave: a.titulo for a in kb.listar(db, "es")}
    return metricas_repository.metricas(db, dias, titulos)
