# app/api/almacen.py
# Endpoints del módulo de almacén (CUS-14): trama, escaneo, conciliación, cierre.
from typing import List, Optional

from fastapi import APIRouter, Depends, File, UploadFile, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_current_almacen
from app.models.usuario import Usuario
from app.services import almacen_service
from app.schemas.almacen import (
    EscaneoRequest,
    EscaneoResponse,
    TramaImportResponse,
    ConciliacionResponse,
    CerrarIngresoResponse,
    RecojoAlmacenItem,
)

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
