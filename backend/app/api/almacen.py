from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_current_almacen
from app.models.usuario import Usuario
from app.services import almacen_service, retorno_service, recojo_service, dashboard_service, pedido_service
from app.schemas.almacen import (
    EscaneoRequest,
    ConciliacionResponse,
    ConfirmarIngresoRequest,
    ConfirmarIngresoResponse,
    RecojoAlmacenItem,
    RutaRetornoItem,
    RetornoRutaResponse,
    EscaneoRetornoResponse,
)
from app.schemas.recojo import SolicitudArmarItem, AsignarRutaRecojoRequest, AsignarRutaRecojoResponse
from app.schemas.dashboard import ConductorUbicacion

router = APIRouter()


@router.get("/recojos", response_model=List[RecojoAlmacenItem])
def listar_recojos(estado: Optional[str] = Query(None), db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_almacen)):
    """Lista los recojos del módulo de almacén (RECOGIDO por ingresar + INGRESADO)."""
    return almacen_service.listar_recojos(db, estado)


@router.get("/recojos/{recojo_id}/conciliacion", response_model=ConciliacionResponse)
def obtener_conciliacion(recojo_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_almacen)):
    """Conciliación detallada de un recojo."""
    return almacen_service.obtener_conciliacion(db, recojo_id)


@router.post("/recojos/{recojo_id}/confirmar-ingreso", response_model=ConfirmarIngresoResponse)
def confirmar_ingreso(
    recojo_id: int,
    datos: ConfirmarIngresoRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_almacen),
):
    """Confirma ingreso manual: marca faltantes como OBSERVADO, resto como LISTO_PARA_ENVIO; geocodifica en segundo plano."""
    resultado = almacen_service.confirmar_ingreso(db, recojo_id, datos.referencias_faltantes, usuario.id)
    background_tasks.add_task(recojo_service.geocodificar_pedidos_recojo, recojo_id)
    return resultado


@router.post("/pedidos/{pedido_id}/resolver-observado")
def resolver_observado(pedido_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_almacen)):
    """Resuelve un pedido OBSERVADO (ya aclarado): lo pasa a LISTO_PARA_ENVIO."""
    return pedido_service.resolver_observado(db, pedido_id, usuario.id)


@router.get("/retornos/rutas", response_model=List[RutaRetornoItem])
def listar_rutas_retorno(db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_almacen)):
    """Rutas de entrega con paquetes FALLIDO pendientes de retorno."""
    return retorno_service.listar_rutas(db)


@router.get("/retornos/rutas/{ruta_id}", response_model=RetornoRutaResponse)
def obtener_retorno_ruta(ruta_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_almacen)):
    """Detalle del retorno de una ruta (sus FALLIDO con estado de retorno)."""
    return retorno_service.obtener_retorno(db, ruta_id)


@router.post("/retornos/rutas/{ruta_id}/escanear", response_model=EscaneoRetornoResponse)
def escanear_retorno(ruta_id: int, datos: EscaneoRequest, db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_almacen)):
    """Escanea un paquete devuelto y lo marca como retornado."""
    return retorno_service.escanear(db, ruta_id, datos.codigo, usuario.id)


@router.get("/solicitudes", response_model=List[SolicitudArmarItem])
def listar_solicitudes_armar(db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_almacen)):
    """Lista solicitudes de recojo en estado SOLICITADO para armar la ruta."""
    return recojo_service.listar_para_armar(db)


@router.post("/solicitudes/asignar-ruta", response_model=AsignarRutaRecojoResponse)
def asignar_ruta_recojo(datos: AsignarRutaRecojoRequest, db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_almacen)):
    """Arma la ruta de recojo asignando conductor y vehículo a las solicitudes seleccionadas."""
    return recojo_service.asignar_ruta_recojo(db, datos, usuario.id)


@router.get("/flota/ubicaciones-recojo", response_model=List[ConductorUbicacion])
def ubicaciones_recojo(db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_almacen)):
    """Posiciones en vivo de los conductores en rutas de RECOJO activas."""
    return dashboard_service.obtener_ubicaciones_flota(db, tipo="RECOJO")
