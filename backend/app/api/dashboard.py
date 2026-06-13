# app/api/dashboard.py
# Expone el módulo de TRAZABILIDAD para el panel web del admin (Fase 4).
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_current_admin
from app.services import dashboard_service
from app.schemas.dashboard import FlotaResponse, ResumenResponse, HistorialPedidoResponse

router = APIRouter()


@router.get("/resumen", response_model=ResumenResponse, dependencies=[Depends(get_current_admin)])
def obtener_resumen(db: Session = Depends(get_db)):
    """CUS-33: KPIs globales (pedidos por estado y conteo de rutas)."""
    return dashboard_service.obtener_resumen(db)


@router.get("/flota", response_model=FlotaResponse, dependencies=[Depends(get_current_admin)])
def obtener_flota(db: Session = Depends(get_db)):
    """CUS-33: estado y avance (%) de todas las rutas de la flota."""
    return dashboard_service.obtener_flota(db)


@router.get(
    "/pedidos/{codigo}/historial",
    response_model=HistorialPedidoResponse,
    dependencies=[Depends(get_current_admin)],
)
def obtener_historial(codigo: str, db: Session = Depends(get_db)):
    """CUS-35: línea de tiempo completa de un paquete (por su código PD-001)."""
    return dashboard_service.obtener_historial(db, codigo)
