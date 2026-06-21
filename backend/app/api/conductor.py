# app/api/conductor.py
# Expone los endpoints que consume EXCLUSIVAMENTE la App Móvil del conductor (toda la Fase 3).
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
    ValidacionQRRequest,
    ValidacionQRResponse,
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


# --- Reporta la posición actual del conductor (mapa de flota en vivo) ---
@router.post("/ubicacion")
def reportar_ubicacion(
    datos: UbicacionRequest,
    db: Session = Depends(get_db),
    conductor: Usuario = Depends(get_current_conductor),
):
    """La app móvil envía la posición del conductor (foreground) cada ~12 s."""
    return conductor_service.registrar_ubicacion(db, conductor.id, datos)


# --- Perfil del propio conductor (para el header/perfil de la app) ---
@router.get("/perfil", response_model=ConductorResponse)
def mi_perfil(
    db: Session = Depends(get_db),
    conductor: Usuario = Depends(get_current_conductor),
):
    return conductor_service.obtener_uno(db, conductor)


# --- CUS-06: motivos de rechazo del catálogo (para el reporte de falla en la app) ---
@router.get("/motivos", response_model=List[str])
def listar_motivos(
    db: Session = Depends(get_db),
    conductor: Usuario = Depends(get_current_conductor),
):
    """Devuelve los textos de los motivos de rechazo configurados por el admin, para
    que la app los muestre al reportar una entrega fallida (antes estaban fijos)."""
    return [m["texto"] for m in parametro_service.listar_motivos(db)]


# --- Reporta una falla de un pedido (incidencia) ---
@router.post("/reportes", response_model=ReporteResponse)
def crear_reporte(
    datos: ReporteCreate,
    db: Session = Depends(get_db),
    conductor: Usuario = Depends(get_current_conductor),
):
    return reporte_service.crear(db, conductor.id, datos)


# --- Lista los reportes del propio conductor (para ver la respuesta del admin) ---
@router.get("/reportes", response_model=List[ReporteResponse])
def mis_reportes(
    db: Session = Depends(get_db),
    conductor: Usuario = Depends(get_current_conductor),
):
    return reporte_service.listar_mios(db, conductor.id)


# --- CUS-21: el conductor descarga/consulta su ruta activa ---
@router.get("/ruta-activa", response_model=RutaActivaResponse)
def consultar_ruta_activa(
    db: Session = Depends(get_db),
    conductor: Usuario = Depends(get_current_conductor),
):
    return ruta_service.obtener_resumen_ruta_activa(db, conductor.id)


# --- CUS-24: manifiesto detallado de la ruta activa ---
@router.get("/ruta-activa/manifiesto", response_model=ManifiestoResponse)
def consultar_manifiesto(
    db: Session = Depends(get_db),
    conductor: Usuario = Depends(get_current_conductor),
):
    return ruta_service.obtener_manifiesto(db, conductor.id)


# --- CUS-25: coordenadas de navegación (waypoints para el mapa) ---
@router.get("/ruta-activa/navegacion", response_model=NavegacionResponse)
def consultar_navegacion(
    db: Session = Depends(get_db),
    conductor: Usuario = Depends(get_current_conductor),
):
    return ruta_service.obtener_navegacion(db, conductor.id)


# --- CUS-22: validación de paquete por QR en almacén (Fase 3.2) ---
@router.post("/almacen/validar-qr", response_model=ValidacionQRResponse)
def validar_paquete_qr(
    solicitud: ValidacionQRRequest,
    db: Session = Depends(get_db),
    conductor: Usuario = Depends(get_current_conductor),
):
    return ruta_service.validar_paquete_qr(db, conductor.id, solicitud.codigo)


# --- CUS-26: marcar entrega ENTREGADO / FALLIDO (Fase 3.3) ---
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


# --- CUS-29: carga de foto POD como evidencia (Fase 3.3) ---
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


# --- CUS-28: cierre de la ruta del día (Fase 3.4) ---
@router.post("/ruta-activa/finalizar", response_model=CierreRutaResponse)
def finalizar_ruta(
    db: Session = Depends(get_db),
    conductor: Usuario = Depends(get_current_conductor),
):
    return ruta_service.finalizar_ruta(db, conductor.id)


# --- CUS-30: el conductor reporta un auxilio mecánico (pausa su ruta) ---
@router.post("/incidencias", response_model=IncidenciaResponse)
def reportar_incidencia(
    datos: IncidenciaCreate,
    db: Session = Depends(get_db),
    conductor: Usuario = Depends(get_current_conductor),
):
    """Crea una incidencia sobre la ruta activa del conductor; la ruta queda pausada."""
    return incidencia_service.reportar(db, conductor.id, datos)


# --- CUS-30: foto opcional de la avería ---
@router.post("/incidencias/{incidencia_id}/evidencia", response_model=IncidenciaResponse)
async def cargar_evidencia_incidencia(
    incidencia_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    conductor: Usuario = Depends(get_current_conductor),
):
    """Adjunta la foto de la avería a una incidencia del conductor."""
    contenido = await file.read()
    return incidencia_service.guardar_evidencia(db, incidencia_id, conductor.id, contenido, file.filename)


# --- CUS-30: el conductor reanuda la ruta (cierra la incidencia) ---
@router.post("/incidencias/{incidencia_id}/reanudar", response_model=IncidenciaResponse)
def reanudar_ruta(
    incidencia_id: int,
    datos: ResolverIncidenciaRequest,
    db: Session = Depends(get_db),
    conductor: Usuario = Depends(get_current_conductor),
):
    """Reanuda la ruta del conductor marcando la incidencia como resuelta."""
    return incidencia_service.reanudar(db, incidencia_id, conductor.id, datos.nota)


# --- CUS-12: manifiesto de la ruta de recojo activa ---
@router.get("/recojo/manifiesto", response_model=ManifiestoRecojoResponse)
def consultar_manifiesto_recojo(
    db: Session = Depends(get_db),
    conductor: Usuario = Depends(get_current_conductor),
):
    """Devuelve los puntos de origen de la ruta de recojo activa (ordenados por secuencia)."""
    return recojo_service.obtener_manifiesto_recojo(db, conductor.id)


# --- CUS-19 (recojo): optimizar la secuencia desde la posición del conductor ---
@router.post("/recojo/optimizar", response_model=OptimizacionResponse)
def optimizar_recojo(
    solicitud: OptimizacionRequest,
    db: Session = Depends(get_db),
    conductor: Usuario = Depends(get_current_conductor),
):
    """Optimiza el orden de la ruta de recojo activa del conductor."""
    return recojo_service.optimizar_recojo(db, solicitud, conductor.id)


# --- CUS-12: recepción condicionada en origen (cantidad declarada + foto de la guía) ---
@router.post("/recojo/{recojo_id}/recepcion", response_model=RecepcionResponse)
async def registrar_recepcion(
    recojo_id: int,
    cantidad_declarada: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    conductor: Usuario = Depends(get_current_conductor),
):
    """Registra el recojo a bulto cerrado: cantidad declarada + foto de la Guía de Remisión."""
    contenido = await file.read()
    return recojo_service.registrar_recepcion(
        db, conductor.id, recojo_id, cantidad_declarada, contenido, file.filename
    )
