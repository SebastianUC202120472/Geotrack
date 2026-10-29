# Rutas HTTP del modulo de catalogo y capacidad (Idea 3).
# El router solo valida, autoriza y responde: la logica vive en el servicio.
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_current_almacen
from app.core.config import settings
from app.db.database import get_db
from app.models.usuario import Usuario
from app.schemas.capacidad import (
    AuditoriaResponse,
    CalculoRequest,
    ConfiguracionResponse,
    ConfiguracionUpdateRequest,
    FlotaVehiculoResponse,
    FiltrosPedidos,
    ModeloCreateRequest,
    ModeloUpdateRequest,
    ModeloVehiculo,
    PlanCapacidadResponse,
    TipoVehiculoEnum,
    VinculacionPlacaRequest,
    VinculacionResponse,
)
from app.services import capacidad_service

router = APIRouter()


def incluir_router(app) -> bool:
    """Registra el modulo si la bandera esta encendida. Recibe la app FastAPI.

    Devuelve True si lo registro. Permite apagar la Idea 3 sin tocar el nucleo.
    """
    if not settings.MODULO_CAPACIDAD_ENABLED:
        return False
    app.include_router(router, prefix="/api/modulo-capacidad")
    return True


@router.get("/salud", tags=["Modulo capacidad"])
def salud():
    """Indicador publico de que el modulo esta activo. Sin parametros."""
    return {"modulo": "capacidad", "habilitado": True}


# ---------------------------------------------------------------------------
# Catalogo
# ---------------------------------------------------------------------------


@router.get(
    "/catalogo",
    response_model=List[ModeloVehiculo],
    tags=["Modulo capacidad"],
)
def listar_catalogo(
    busqueda: Optional[str] = Query(None, max_length=80),
    marca: Optional[str] = Query(None, max_length=60),
    tipo: Optional[TipoVehiculoEnum] = Query(None),
    solo_verificados: bool = Query(False),
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_almacen),
):
    """Lista el catalogo completo (JSON base + cambios del panel)."""
    modelos = capacidad_service.catalogo_completo(db)
    return capacidad_service.filtrar_catalogo(
        modelos, busqueda=busqueda, marca=marca,
        tipo=tipo.value if tipo else None, solo_verificados=solo_verificados,
    )


@router.get(
    "/catalogo/{modelo_id}",
    response_model=ModeloVehiculo,
    tags=["Modulo capacidad"],
)
def obtener_modelo(
    modelo_id: str,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_almacen),
):
    """Devuelve la ficha de un modelo del catalogo."""
    modelo = capacidad_service.obtener_modelo(db, modelo_id)
    if modelo is None:
        raise HTTPException(status_code=404, detail="El modelo no existe en el catalogo.")
    return modelo


@router.post(
    "/catalogo",
    response_model=ModeloVehiculo,
    status_code=status.HTTP_201_CREATED,
    tags=["Modulo capacidad"],
)
def crear_modelo(
    datos: ModeloCreateRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_admin),
):
    """Agrega un modelo al catalogo (solo administradores)."""
    return capacidad_service.crear_modelo(db, datos, usuario.correo)


@router.patch(
    "/catalogo/{modelo_id}",
    response_model=ModeloVehiculo,
    tags=["Modulo capacidad"],
)
def actualizar_modelo(
    modelo_id: str,
    datos: ModeloUpdateRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_admin),
):
    """Edita un modelo; en los del JSON base guarda una copia propia."""
    return capacidad_service.actualizar_modelo(db, modelo_id, datos, usuario.correo)


@router.delete("/catalogo/{modelo_id}", tags=["Modulo capacidad"])
def eliminar_modelo(
    modelo_id: str,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_admin),
):
    """Borra un modelo agregado desde el panel (los base no se borran)."""
    capacidad_service.eliminar_modelo(db, modelo_id, usuario.correo)
    return {"mensaje": "Modelo eliminado"}


# ---------------------------------------------------------------------------
# Flota y vinculaciones
# ---------------------------------------------------------------------------


@router.get(
    "/flota",
    response_model=List[FlotaVehiculoResponse],
    tags=["Modulo capacidad"],
)
def listar_flota(
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_almacen),
):
    """Lista la flota y, si tiene, su modelo vinculado."""
    return capacidad_service.listar_flota(db)


@router.get(
    "/vinculaciones",
    response_model=List[VinculacionResponse],
    tags=["Modulo capacidad"],
)
def listar_vinculaciones(
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_almacen),
):
    """Historial de placas vinculadas a modelos."""
    return capacidad_service.listar_vinculaciones(db)


@router.post(
    "/vinculaciones",
    response_model=VinculacionResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Modulo capacidad"],
)
def crear_vinculacion(
    datos: VinculacionPlacaRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_admin),
):
    """Vincula una placa de la flota con un modelo (solo administradores)."""
    fila = capacidad_service.vincular(db, datos, usuario.correo)
    return capacidad_service.respuesta_vinculacion(db, fila)


@router.post(
    "/vincular",
    response_model=VinculacionResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Modulo capacidad"],
    include_in_schema=False,
)
def vincular_compatibilidad(
    datos: VinculacionPlacaRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_admin),
):
    """Alias del endpoint anterior, se mantiene por compatibilidad."""
    fila = capacidad_service.vincular(db, datos, usuario.correo)
    return capacidad_service.respuesta_vinculacion(db, fila)


@router.delete("/vinculaciones/{vinculacion_id}", tags=["Modulo capacidad"])
def eliminar_vinculacion(
    vinculacion_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_admin),
):
    """Quita la vinculacion de una placa (solo administradores)."""
    capacidad_service.eliminar_vinculacion(db, vinculacion_id, usuario.correo)
    return {"mensaje": "Vinculacion eliminada"}


# ---------------------------------------------------------------------------
# Configuracion
# ---------------------------------------------------------------------------


@router.get(
    "/configuracion",
    response_model=ConfiguracionResponse,
    tags=["Modulo capacidad"],
)
def obtener_configuracion(
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_almacen),
):
    """Devuelve el factor de aprovechamiento y los topes de planificacion."""
    return capacidad_service.configuracion_dict(capacidad_service.obtener_configuracion(db))


@router.put(
    "/configuracion",
    response_model=ConfiguracionResponse,
    tags=["Modulo capacidad"],
)
def actualizar_configuracion(
    datos: ConfiguracionUpdateRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_admin),
):
    """Actualiza los parametros de planificacion (solo administradores)."""
    config = capacidad_service.actualizar_configuracion(db, datos, usuario.correo)
    return capacidad_service.configuracion_dict(config)


# ---------------------------------------------------------------------------
# Calculadora y planificacion
# ---------------------------------------------------------------------------


@router.post(
    "/calcular",
    response_model=PlanCapacidadResponse,
    tags=["Modulo capacidad"],
)
def calcular(
    datos: CalculoRequest,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_almacen),
):
    """Calcula viajes y alertas para un modelo o una placa de la flota."""
    return capacidad_service.calcular(db, datos)


@router.get(
    "/planificacion",
    response_model=PlanCapacidadResponse,
    tags=["Modulo capacidad"],
)
def planificacion(
    estado: Optional[str] = Query(None, max_length=40),
    distrito: Optional[str] = Query(None, max_length=100),
    fecha: Optional[date] = Query(None),
    limite: Optional[int] = Query(None, ge=1, le=5000),
    demo_pedidos: Optional[int] = Query(None, ge=1, le=5000),
    demo_vehiculos: Optional[int] = Query(None, ge=1, le=50),
    factor_aprovechamiento: Optional[float] = Query(None, ge=0.5, le=1.0),
    max_paradas_por_viaje: Optional[int] = Query(None, ge=1, le=100),
    max_viajes_por_dia: Optional[int] = Query(None, ge=1, le=20),
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_almacen),
):
    """Planifica el dia con los pedidos reales y la flota vinculada."""
    filtros = FiltrosPedidos(
        estado=estado, distrito=distrito, fecha=fecha, limite=limite
    )
    return capacidad_service.planificacion(
        db,
        filtros,
        demo_pedidos=demo_pedidos,
        demo_vehiculos=demo_vehiculos,
        factor_aprovechamiento=factor_aprovechamiento,
        max_paradas_por_viaje=max_paradas_por_viaje,
        max_viajes_por_dia=max_viajes_por_dia,
    )


# ---------------------------------------------------------------------------
# Auditoria
# ---------------------------------------------------------------------------


@router.get(
    "/auditoria",
    response_model=List[AuditoriaResponse],
    tags=["Modulo capacidad"],
)
def listar_auditoria(
    limite: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_admin),
):
    """Ultimos cambios del modulo (solo administradores)."""
    return capacidad_service.historial_auditoria(db, limite)