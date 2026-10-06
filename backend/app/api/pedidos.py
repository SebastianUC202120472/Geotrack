from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_current_admin
from app.models.usuario import Usuario
from app.services import pedido_service
from app.schemas.pedido import (
    PedidoResponse,
    GeocodificacionResponse,
    ZonasResponse,
    ZonasPorEnrutarResponse,
    UbicacionManualRequest,
    BuscarDireccionResponse,
)
from typing import List, Optional

router = APIRouter()


@router.get("/", response_model=List[PedidoResponse], dependencies=[Depends(get_current_admin)])
def listar_pedidos(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    busqueda: Optional[str] = None,
    distrito: Optional[str] = None,
    estado: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Lista paginada de pedidos (mas nuevos primero). Recibe offset, limite (max 1000) y filtros opcionales."""
    return pedido_service.listar_pedidos(db, skip=skip, limit=limit, busqueda=busqueda, distrito=distrito, estado=estado)


@router.post("/geocodificar", response_model=GeocodificacionResponse)
def procesar_geocodificacion(db: Session = Depends(get_db), admin: Usuario = Depends(get_current_admin)):
    """Convierte direcciones en coordenadas y deduce el distrito."""
    return pedido_service.procesar_geocodificacion(db, usuario_id=admin.id)


@router.get("/zonas", response_model=ZonasResponse, dependencies=[Depends(get_current_admin)])
def agrupar_pedidos_por_zona(db: Session = Depends(get_db)):
    """Agrupa los pedidos geocodificados por distrito."""
    return pedido_service.agrupar_por_zona(db)


@router.get("/zonas/por-enrutar", response_model=ZonasPorEnrutarResponse, dependencies=[Depends(get_current_admin)])
def zonas_por_enrutar(db: Session = Depends(get_db)):
    """Zonas con pedidos pendientes o asignados, contadas en el servidor."""
    return pedido_service.zonas_por_enrutar(db)


@router.get("/por-ubicar", response_model=List[PedidoResponse], dependencies=[Depends(get_current_admin)])
def listar_por_ubicar(db: Session = Depends(get_db)):
    """Pedidos cuya dirección no se pudo geocodificar, para ubicar a mano."""
    return pedido_service.listar_para_ubicar(db)


@router.get("/buscar-direccion", response_model=BuscarDireccionResponse, dependencies=[Depends(get_current_admin)])
def buscar_direccion(q: str, db: Session = Depends(get_db)):
    """Geocodifica un texto de búsqueda para ubicar el pin en el mapa. Recibe q (texto)."""
    return pedido_service.buscar_direccion(q)


@router.patch("/{pedido_id}/ubicacion")
def fijar_ubicacion(pedido_id: int, datos: UbicacionManualRequest, db: Session = Depends(get_db), admin: Usuario = Depends(get_current_admin)):
    """Fija manualmente la ubicación de un pedido y lo deja listo para rutear. Recibe pedido_id y lat/lng."""
    return pedido_service.fijar_ubicacion(db, pedido_id, datos.latitud, datos.longitud, datos.direccion, usuario_id=admin.id)


@router.post("/{pedido_id}/reprogramar")
def reprogramar_pedido(pedido_id: int, db: Session = Depends(get_db), admin: Usuario = Depends(get_current_admin)):
    """Vuelve un pedido FALLIDO a LISTO_PARA_ENVIO para reintentarlo. Recibe pedido_id."""
    return pedido_service.reprogramar(db, pedido_id, usuario_id=admin.id)


@router.post("/{pedido_id}/cancelar")
def cancelar_pedido(pedido_id: int, db: Session = Depends(get_db), admin: Usuario = Depends(get_current_admin)):
    """Cancela definitivamente un pedido FALLIDO. Recibe pedido_id."""
    return pedido_service.cancelar(db, pedido_id, usuario_id=admin.id)
