from typing import List
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_current_admin
from app.services import dashboard_service, liquidacion_service
from app.schemas.dashboard import (
    FlotaResponse,
    ResumenResponse,
    HistorialPedidoResponse,
    ClienteSeguimiento,
    ConductorUbicacion,
    LiquidacionRequest,
    LiquidacionResponse,
    EficienciaConductor,
)

router = APIRouter()


@router.get("/resumen", response_model=ResumenResponse, dependencies=[Depends(get_current_admin)])
def obtener_resumen(db: Session = Depends(get_db)):
    """Devuelve KPIs globales: pedidos por estado y conteo de rutas."""
    return dashboard_service.obtener_resumen(db)


@router.get("/flota", response_model=FlotaResponse, dependencies=[Depends(get_current_admin)])
def obtener_flota(db: Session = Depends(get_db)):
    """Devuelve estado y avance (%) de todas las rutas de la flota."""
    return dashboard_service.obtener_flota(db)


@router.get("/clientes", response_model=List[ClienteSeguimiento], dependencies=[Depends(get_current_admin)])
def obtener_por_cliente(db: Session = Depends(get_db)):
    """Devuelve seguimiento de repartos agregado por empresa cliente."""
    return dashboard_service.obtener_por_cliente(db)


@router.get("/flota/ubicaciones", response_model=List[ConductorUbicacion], dependencies=[Depends(get_current_admin)])
def obtener_ubicaciones_flota(db: Session = Depends(get_db)):
    """Devuelve posicion en vivo de conductores activos y sus paradas pendientes."""
    return dashboard_service.obtener_ubicaciones_flota(db)


@router.post("/clientes/liquidacion", response_model=LiquidacionResponse, dependencies=[Depends(get_current_admin)])
def generar_liquidacion(datos: LiquidacionRequest, db: Session = Depends(get_db)):
    """Genera el .xlsx de liquidacion de un cliente. Recibe cliente y periodo."""
    return liquidacion_service.generar(db, datos.cliente, datos.periodo_inicio, datos.periodo_fin)


@router.get("/liquidaciones/{liquidacion_id}/descarga", dependencies=[Depends(get_current_admin)])
def descargar_liquidacion(liquidacion_id: int, db: Session = Depends(get_db)):
    """Descarga el .xlsx de una liquidacion. Recibe liquidacion_id."""
    ruta, nombre = liquidacion_service.ruta_archivo(db, liquidacion_id)
    return FileResponse(
        ruta,
        filename=nombre,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@router.get(
    "/pedidos/{codigo}/historial",
    response_model=HistorialPedidoResponse,
    dependencies=[Depends(get_current_admin)],
)
def obtener_historial(codigo: str, db: Session = Depends(get_db)):
    """Devuelve el historial completo de un pedido. Recibe su codigo."""
    return dashboard_service.obtener_historial(db, codigo)


@router.get("/eficiencia-conductores", response_model=List[EficienciaConductor], dependencies=[Depends(get_current_admin)])
def obtener_eficiencia_conductores(db: Session = Depends(get_db)):
    """Devuelve km y ahorro de combustible acumulados por conductor."""
    return dashboard_service.obtener_eficiencia_conductores(db)
