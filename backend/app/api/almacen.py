# app/api/almacen.py
# Endpoints del módulo de almacén (CUS-14): trama, escaneo, conciliación, cierre.
from typing import List, Optional

from fastapi import APIRouter, Depends, File, UploadFile, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_current_almacen
from app.models.usuario import Usuario
from app.services import almacen_service, retorno_service, recojo_service
from app.schemas.almacen import (
    EscaneoRequest,
    EscaneoResponse,
    TramaImportResponse,
    ConciliacionResponse,
    CerrarIngresoResponse,
    RecojoAlmacenItem,
    RutaRetornoItem,
    RetornoRutaResponse,
    EscaneoRetornoResponse,
)
from app.schemas.recojo import SolicitudArmarItem, AsignarRutaRecojoRequest, AsignarRutaRecojoResponse

router = APIRouter()


@router.get("/recojos", response_model=List[RecojoAlmacenItem])
def listar_recojos(estado: Optional[str] = Query(None), db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_almacen)):
    """Lista los recojos del módulo de almacén (RECOGIDO por ingresar + INGRESADO)."""
    return almacen_service.listar_recojos(db, estado)


@router.post("/recojos/{recojo_id}/trama", response_model=TramaImportResponse)
async def importar_trama(recojo_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_almacen)):
    """Importa la trama (códigos esperados) de un recojo desde un Excel."""
    contenido = await file.read()
    return almacen_service.importar_trama(db, recojo_id, contenido, file.filename, usuario.id)


@router.get("/recojos/{recojo_id}/conciliacion", response_model=ConciliacionResponse)
def obtener_conciliacion(recojo_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_almacen)):
    """Conciliación detallada de un recojo."""
    return almacen_service.obtener_conciliacion(db, recojo_id)


@router.post("/recojos/{recojo_id}/escanear", response_model=EscaneoResponse)
def escanear(recojo_id: int, datos: EscaneoRequest, db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_almacen)):
    """Escanea un paquete y lo cruza contra la trama del recojo."""
    return almacen_service.escanear(db, recojo_id, datos.codigo, usuario.id)


@router.post("/recojos/{recojo_id}/cerrar-ingreso", response_model=CerrarIngresoResponse)
def cerrar_ingreso(recojo_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_almacen)):
    """Cierra el ingreso del recojo (pasa a INGRESADO)."""
    return almacen_service.cerrar_ingreso(db, recojo_id, usuario.id)


# --- CUS-32: logística inversa (retornos de ruta) ---
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


# --- CUS-11: armado de ruta de recojo (responsabilidad del almacén) ---
@router.get("/solicitudes", response_model=List[SolicitudArmarItem])
def listar_solicitudes_armar(db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_almacen)):
    """Lista las solicitudes de recojo en SOLICITADO con su número de pedidos,
    para que el almacén elija cuáles incluir en la ruta de recojo."""
    return recojo_service.listar_para_armar(db)


@router.post("/solicitudes/asignar-ruta", response_model=AsignarRutaRecojoResponse)
def asignar_ruta_recojo(datos: AsignarRutaRecojoRequest, db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_almacen)):
    """Arma la ruta de recojo (conductor + vehículo) con las solicitudes seleccionadas.
    Recibe: recojo_ids, conductor_id, vehiculo_placa y nombre opcional."""
    return recojo_service.asignar_ruta_recojo(db, datos, usuario.id)
