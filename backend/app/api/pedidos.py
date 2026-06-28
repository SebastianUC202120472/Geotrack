# app/api/pedidos.py
# Expone las URLs del módulo Inbound (gestión de pedidos del admin).
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_current_admin
from app.models.usuario import Usuario
from app.services import pedido_service
from app.schemas.pedido import (
    PedidoResponse,
    GeocodificacionResponse,
    ZonasResponse,
    UbicacionManualRequest,
    BuscarDireccionResponse,
)
from typing import List

router = APIRouter()


@router.get("/", response_model=List[PedidoResponse], dependencies=[Depends(get_current_admin)])
def listar_pedidos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Lista paginada de pedidos."""
    return pedido_service.listar_pedidos(db, skip=skip, limit=limit)


@router.post("/geocodificar", response_model=GeocodificacionResponse)
def procesar_geocodificacion(db: Session = Depends(get_db), admin: Usuario = Depends(get_current_admin)):
    """Convierte las direcciones en coordenadas y deduce el distrito (CUS-15)."""
    return pedido_service.procesar_geocodificacion(db, usuario_id=admin.id)


@router.get("/zonas", response_model=ZonasResponse, dependencies=[Depends(get_current_admin)])
def agrupar_pedidos_por_zona(db: Session = Depends(get_db)):
    """Agrupa los pedidos geocodificados por distrito (CUS-16)."""
    return pedido_service.agrupar_por_zona(db)


@router.get("/por-ubicar", response_model=List[PedidoResponse], dependencies=[Depends(get_current_admin)])
def listar_por_ubicar(db: Session = Depends(get_db)):
    """CUS-17: pedidos cuya dirección no se pudo geocodificar (para resolver a mano)."""
    return pedido_service.listar_para_ubicar(db)


@router.get("/buscar-direccion", response_model=BuscarDireccionResponse, dependencies=[Depends(get_current_admin)])
def buscar_direccion(q: str, db: Session = Depends(get_db)):
    """CUS-17: geocodifica un texto de búsqueda para ubicar el pin en el mapa."""
    return pedido_service.buscar_direccion(q)


@router.patch("/{pedido_id}/ubicacion")
def fijar_ubicacion(pedido_id: int, datos: UbicacionManualRequest, db: Session = Depends(get_db), admin: Usuario = Depends(get_current_admin)):
    """CUS-17: fija a mano la ubicación (lat/lng) de un pedido y lo deja listo para rutear."""
    return pedido_service.fijar_ubicacion(db, pedido_id, datos.latitud, datos.longitud, datos.direccion, usuario_id=admin.id)


@router.post("/{pedido_id}/reprogramar")
def reprogramar_pedido(pedido_id: int, db: Session = Depends(get_db), admin: Usuario = Depends(get_current_admin)):
    """CUS-31: vuelve un pedido FALLIDO a PENDIENTE para reintentarlo (reasignar)."""
    return pedido_service.reprogramar(db, pedido_id, usuario_id=admin.id)


@router.post("/{pedido_id}/cancelar")
def cancelar_pedido(pedido_id: int, db: Session = Depends(get_db), admin: Usuario = Depends(get_current_admin)):
    """CUS-31: cancela definitivamente un pedido FALLIDO (estado CANCELADO)."""
    return pedido_service.cancelar(db, pedido_id, usuario_id=admin.id)
