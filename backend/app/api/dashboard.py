# app/api/dashboard.py
# Expone el módulo de TRAZABILIDAD para el panel web del admin (Fase 4).
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
    """CUS-33: KPIs globales (pedidos por estado y conteo de rutas)."""
    return dashboard_service.obtener_resumen(db)


@router.get("/flota", response_model=FlotaResponse, dependencies=[Depends(get_current_admin)])
def obtener_flota(db: Session = Depends(get_db)):
    """CUS-33: estado y avance (%) de todas las rutas de la flota."""
    return dashboard_service.obtener_flota(db)


@router.get("/clientes", response_model=List[ClienteSeguimiento], dependencies=[Depends(get_current_admin)])
def obtener_por_cliente(db: Session = Depends(get_db)):
    """Seguimiento de repartos agregado por empresa cliente (entregados / fallidos /
    pendientes / en proceso), no por ruta."""
    return dashboard_service.obtener_por_cliente(db)


@router.get("/flota/ubicaciones", response_model=List[ConductorUbicacion], dependencies=[Depends(get_current_admin)])
def obtener_ubicaciones_flota(db: Session = Depends(get_db)):
    """Posición en vivo de cada conductor con ruta activa + sus paradas pendientes."""
    return dashboard_service.obtener_ubicaciones_flota(db)


@router.post("/clientes/liquidacion", response_model=LiquidacionResponse, dependencies=[Depends(get_current_admin)])
def generar_liquidacion(datos: LiquidacionRequest, db: Session = Depends(get_db)):
    """CUS-36: genera el reporte de liquidación (.xlsx) de un cliente, lo guarda y
    registra; devuelve la ruta del endpoint autenticado para descargarlo."""
    return liquidacion_service.generar(db, datos.cliente, datos.periodo_inicio, datos.periodo_fin)


@router.get("/liquidaciones/{liquidacion_id}/descarga", dependencies=[Depends(get_current_admin)])
def descargar_liquidacion(liquidacion_id: int, db: Session = Depends(get_db)):
    """CUS-36: descarga el .xlsx de una liquidación. Protegido (solo admin): el archivo
    NO es público porque contiene datos personales de los destinatarios (Ley 29733)."""
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
    """CUS-35: línea de tiempo completa de un paquete (por su código PD-001)."""
    return dashboard_service.obtener_historial(db, codigo)


@router.get("/eficiencia-conductores", response_model=List[EficienciaConductor], dependencies=[Depends(get_current_admin)])
def obtener_eficiencia_conductores(db: Session = Depends(get_db)):
    """CUS-34: eficiencia (km y ahorro de combustible) acumulada por cada conductor."""
    return dashboard_service.obtener_eficiencia_conductores(db)
