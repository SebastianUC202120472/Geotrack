from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from typing import List

from app.db.database import get_db
from app.api.deps import get_current_conductor
from app.models.usuario import Usuario
from app.services import ruta_service, reporte_service, conductor_service, parametro_service, incidencia_service, recojo_service
from app.schemas.ruta import (
    RutaActivaResponse,
    ManifiestoResponse,
    NavegacionResponse,
    ActualizarEstadoRequest,
    GestionParadaResponse,
    CierreRutaResponse,
    OptimizacionRequest,
    OptimizacionResponse,
)
from app.schemas.recojo import ManifiestoRecojoResponse, RecepcionResponse
from app.schemas.reporte import ReporteCreate, ReporteResponse
from app.schemas.incidencia import IncidenciaCreate, ResolverIncidenciaRequest, IncidenciaResponse
from app.schemas.conductor import ConductorResponse, UbicacionRequest

router = APIRouter()


@router.post("/ubicacion")
def reportar_ubicacion(
    datos: UbicacionRequest,
    db: Session = Depends(get_db),
    conductor: Usuario = Depends(get_current_conductor),
):
    """Registra la posicion GPS del conductor. Recibe UbicacionRequest."""
    return conductor_service.registrar_ubicacion(db, conductor.id, datos)


@router.get("/perfil", response_model=ConductorResponse)
def mi_perfil(
    db: Session = Depends(get_db),
    conductor: Usuario = Depends(get_current_conductor),
):
    return conductor_service.obtener_uno(db, conductor)


@router.get("/motivos", response_model=List[str])
def listar_motivos(
    db: Session = Depends(get_db),
    conductor: Usuario = Depends(get_current_conductor),
):
    """Devuelve los motivos de rechazo configurados por el admin."""
    return [m["texto"] for m in parametro_service.listar_motivos(db)]


@router.post("/reportes", response_model=ReporteResponse)
def crear_reporte(
    datos: ReporteCreate,
    db: Session = Depends(get_db),
    conductor: Usuario = Depends(get_current_conductor),
):
    return reporte_service.crear(db, conductor.id, datos)


@router.get("/reportes", response_model=List[ReporteResponse])
def mis_reportes(
    db: Session = Depends(get_db),
    conductor: Usuario = Depends(get_current_conductor),
):
    return reporte_service.listar_mios(db, conductor.id)


@router.get("/ruta-activa", response_model=RutaActivaResponse)
def consultar_ruta_activa(
    db: Session = Depends(get_db),
    conductor: Usuario = Depends(get_current_conductor),
):
    return ruta_service.obtener_resumen_ruta_activa(db, conductor.id)


@router.get("/ruta-activa/manifiesto", response_model=ManifiestoResponse)
def consultar_manifiesto(
    db: Session = Depends(get_db),
    conductor: Usuario = Depends(get_current_conductor),
):
    return ruta_service.obtener_manifiesto(db, conductor.id)


@router.get("/ruta-activa/navegacion", response_model=NavegacionResponse)
def consultar_navegacion(
    db: Session = Depends(get_db),
    conductor: Usuario = Depends(get_current_conductor),
):
    return ruta_service.obtener_navegacion(db, conductor.id)


@router.patch("/paradas/{pedido_id}/estado", response_model=GestionParadaResponse)
def actualizar_estado_parada(
    pedido_id: int,
    solicitud: ActualizarEstadoRequest,
    db: Session = Depends(get_db),
    conductor: Usuario = Depends(get_current_conductor),
):
    return ruta_service.actualizar_estado_parada(
        db, conductor.id, pedido_id, solicitud.estado, solicitud.motivo_fallo
    )


@router.post("/paradas/{pedido_id}/evidencia", response_model=GestionParadaResponse)
async def cargar_evidencia(
    pedido_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    conductor: Usuario = Depends(get_current_conductor),
):
    contenido = await file.read()
    return ruta_service.guardar_evidencia(
        db, conductor.id, pedido_id, contenido, file.filename
    )


@router.post("/ruta-activa/finalizar", response_model=CierreRutaResponse)
def finalizar_ruta(
    db: Session = Depends(get_db),
    conductor: Usuario = Depends(get_current_conductor),
):
    return ruta_service.finalizar_ruta(db, conductor.id)


@router.post("/incidencias", response_model=IncidenciaResponse)
def reportar_incidencia(
    datos: IncidenciaCreate,
    db: Session = Depends(get_db),
    conductor: Usuario = Depends(get_current_conductor),
):
    """Crea una incidencia de auxilio; pausa la ruta activa. Recibe IncidenciaCreate."""
    return incidencia_service.reportar(db, conductor.id, datos)


@router.post("/incidencias/{incidencia_id}/evidencia", response_model=IncidenciaResponse)
async def cargar_evidencia_incidencia(
    incidencia_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    conductor: Usuario = Depends(get_current_conductor),
):
    """Adjunta foto de averia a una incidencia. Recibe incidencia_id y archivo."""
    contenido = await file.read()
    return incidencia_service.guardar_evidencia(db, incidencia_id, conductor.id, contenido, file.filename)


@router.post("/incidencias/{incidencia_id}/reanudar", response_model=IncidenciaResponse)
def reanudar_ruta(
    incidencia_id: int,
    datos: ResolverIncidenciaRequest,
    db: Session = Depends(get_db),
    conductor: Usuario = Depends(get_current_conductor),
):
    """Cierra la incidencia y reanuda la ruta. Recibe incidencia_id y nota opcional."""
    return incidencia_service.reanudar(db, incidencia_id, conductor.id, datos.nota)


@router.get("/recojo/manifiesto", response_model=ManifiestoRecojoResponse)
def consultar_manifiesto_recojo(
    db: Session = Depends(get_db),
    conductor: Usuario = Depends(get_current_conductor),
):
    """Devuelve los puntos de la ruta de recojo activa ordenados por secuencia."""
    return recojo_service.obtener_manifiesto_recojo(db, conductor.id)


@router.post("/recojo/optimizar", response_model=OptimizacionResponse)
def optimizar_recojo(
    solicitud: OptimizacionRequest,
    db: Session = Depends(get_db),
    conductor: Usuario = Depends(get_current_conductor),
):
    """Optimiza el orden de la ruta de recojo activa. Recibe OptimizacionRequest."""
    return recojo_service.optimizar_recojo(db, solicitud, conductor.id)


@router.post("/recojo/{recojo_id}/recepcion", response_model=RecepcionResponse)
async def registrar_recepcion(
    recojo_id: int,
    cantidad_declarada: int = Form(...),
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    conductor: Usuario = Depends(get_current_conductor),
):
    """Registra el recojo con cantidad declarada y fotos de evidencia."""
    archivos = [(await f.read(), f.filename) for f in files]
    return recojo_service.registrar_recepcion(
        db, conductor.id, recojo_id, cantidad_declarada, archivos
    )
