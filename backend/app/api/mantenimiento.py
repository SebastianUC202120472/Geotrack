# Rutas HTTP del modulo de mantenimiento y documentos de la flota (Idea 4).
# El router solo valida, autoriza y responde: la logica vive en el servicio.
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_current_almacen
from app.core.config import settings
from app.db.database import get_db
from app.models.usuario import Usuario
from app.schemas.mantenimiento import (
    AlertaResponse,
    AveriaVehiculoResponse,
    AuditoriaResponse,
    CargaCombustibleCreateRequest,
    CargaCombustibleResponse,
    CargaCombustibleUpdateRequest,
    CompletarMantenimientoRequest,
    ConfiguracionResponse,
    ConfiguracionUpdateRequest,
    CostosFlotaResponse,
    DocumentoCreateRequest,
    DocumentoResponse,
    DocumentoUpdateRequest,
    EstadoDocumentoEnum,
    EstadoMantenimientoEnum,
    FichaVehiculoResponse,
    FlotaEstadoResponse,
    LicenciaResponse,
    MantenimientoCreateRequest,
    MantenimientoResponse,
    MantenimientoUpdateRequest,
    PreventivoCreateRequest,
    PreventivoResponse,
    PreventivoUpdateRequest,
    ResumenResponse,
    TipoCombustibleEnum,
    TipoDocumentoEnum,
    TipoMantenimientoEnum,
)
from app.services import mantenimiento_service

router = APIRouter()


def incluir_router(app) -> bool:
    """Registra el modulo si la bandera esta encendida. Recibe la app FastAPI.

    Devuelve True si lo registro. Permite apagar la Idea 4 sin tocar el nucleo.
    """

    if not settings.MODULO_MANTENIMIENTO_ENABLED:
        return False
    app.include_router(router, prefix="/api/modulo-mantenimiento")
    return True


@router.get("/salud", tags=["Modulo mantenimiento"])
def salud():
    """Indicador publico de que el modulo esta activo. Sin parametros."""

    return {"modulo": "mantenimiento", "habilitado": True}


# ---------------------------------------------------------------------------
# Resumen y estado de la flota
# ---------------------------------------------------------------------------


@router.get(
    "/resumen",
    response_model=ResumenResponse,
    tags=["Modulo mantenimiento"],
)
def obtener_resumen(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_almacen),
):
    """Devuelve los indicadores de documentos y mantenimientos.

    Las alertas de licencias solo se cuentan para el rol admin.
    """

    return mantenimiento_service.resumen(
        db, incluir_licencias=usuario.rol == "admin"
    )


@router.get(
    "/flota",
    response_model=List[FlotaEstadoResponse],
    tags=["Modulo mantenimiento"],
)
def estado_flota(
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_almacen),
):
    """Lista cada vehiculo con su estado documental y de mantenimiento."""

    return mantenimiento_service.estado_flota(db)


@router.get(
    "/flota/{placa}",
    response_model=FichaVehiculoResponse,
    tags=["Modulo mantenimiento"],
)
def ficha_vehiculo(
    placa: str,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_almacen),
):
    """Devuelve la ficha de estado de una unidad: documentos, mantenimientos y costos."""

    return mantenimiento_service.ficha_vehiculo(db, placa)


@router.get(
    "/alertas",
    response_model=List[AlertaResponse],
    tags=["Modulo mantenimiento"],
)
def listar_alertas(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_almacen),
):
    """Devuelve los avisos calculados.

    Las alertas de licencias de conductores solo se incluyen para el rol admin.
    """

    return mantenimiento_service.alertas(
        db, incluir_licencias=usuario.rol == "admin"
    )


@router.get(
    "/licencias",
    response_model=List[LicenciaResponse],
    tags=["Modulo mantenimiento"],
)
def listar_licencias(
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_admin),
):
    """Lista las licencias de conductores con su vencimiento (solo administradores)."""

    return mantenimiento_service.listar_licencias(db)


# ---------------------------------------------------------------------------
# Documentos de la flota
# ---------------------------------------------------------------------------


@router.get(
    "/documentos",
    response_model=List[DocumentoResponse],
    tags=["Modulo mantenimiento"],
)
def listar_documentos(
    placa: Optional[str] = Query(None, max_length=20),
    tipo: Optional[TipoDocumentoEnum] = Query(None),
    estado: Optional[EstadoDocumentoEnum] = Query(None),
    limite: int = Query(200, ge=1, le=500),
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_almacen),
):
    """Lista documentos con filtros por placa, tipo y estado calculado."""

    return mantenimiento_service.listar_documentos(
        db, placa=placa, tipo=tipo, estado=estado, limite=limite
    )


@router.post(
    "/documentos",
    response_model=DocumentoResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Modulo mantenimiento"],
)
def crear_documento(
    datos: DocumentoCreateRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_admin),
):
    """Registra un documento de flota (solo administradores)."""

    return mantenimiento_service.crear_documento(db, datos, usuario.correo)


@router.get(
    "/documentos/{documento_id}",
    response_model=DocumentoResponse,
    tags=["Modulo mantenimiento"],
)
def obtener_documento(
    documento_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_almacen),
):
    """Devuelve un documento por su identificador."""

    return mantenimiento_service.obtener_documento(db, documento_id)


@router.patch(
    "/documentos/{documento_id}",
    response_model=DocumentoResponse,
    tags=["Modulo mantenimiento"],
)
def actualizar_documento(
    documento_id: int,
    datos: DocumentoUpdateRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_admin),
):
    """Edita un documento y deja el cambio en auditoria (solo administradores)."""

    return mantenimiento_service.actualizar_documento(
        db, documento_id, datos, usuario.correo
    )


@router.delete("/documentos/{documento_id}", tags=["Modulo mantenimiento"])
def eliminar_documento(
    documento_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_admin),
):
    """Elimina logicamente un documento (solo administradores)."""

    mantenimiento_service.eliminar_documento(db, documento_id, usuario.correo)
    return {"mensaje": "Documento eliminado"}


# ---------------------------------------------------------------------------
# Mantenimientos
# ---------------------------------------------------------------------------


@router.get(
    "/mantenimientos",
    response_model=List[MantenimientoResponse],
    tags=["Modulo mantenimiento"],
)
def listar_mantenimientos(
    placa: Optional[str] = Query(None, max_length=20),
    tipo: Optional[TipoMantenimientoEnum] = Query(None),
    estado: Optional[EstadoMantenimientoEnum] = Query(None),
    desde: Optional[date] = Query(None),
    hasta: Optional[date] = Query(None),
    limite: int = Query(200, ge=1, le=500),
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_almacen),
):
    """Lista mantenimientos con filtros por placa, tipo, estado y fechas."""

    return mantenimiento_service.listar_mantenimientos(
        db,
        placa=placa,
        tipo=tipo,
        estado=estado,
        desde=desde,
        hasta=hasta,
        limite=limite,
    )


@router.post(
    "/mantenimientos",
    response_model=MantenimientoResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Modulo mantenimiento"],
)
def crear_mantenimiento(
    datos: MantenimientoCreateRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_admin),
):
    """Programa o registra un mantenimiento (solo administradores)."""

    return mantenimiento_service.crear_mantenimiento(db, datos, usuario.correo)


@router.get(
    "/mantenimientos/{mantenimiento_id}",
    response_model=MantenimientoResponse,
    tags=["Modulo mantenimiento"],
)
def obtener_mantenimiento(
    mantenimiento_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_almacen),
):
    """Devuelve un mantenimiento por su identificador."""

    return mantenimiento_service.obtener_mantenimiento(db, mantenimiento_id)


@router.patch(
    "/mantenimientos/{mantenimiento_id}",
    response_model=MantenimientoResponse,
    tags=["Modulo mantenimiento"],
)
def actualizar_mantenimiento(
    mantenimiento_id: int,
    datos: MantenimientoUpdateRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_admin),
):
    """Edita un mantenimiento (solo administradores)."""

    return mantenimiento_service.actualizar_mantenimiento(
        db, mantenimiento_id, datos, usuario.correo
    )


@router.post(
    "/mantenimientos/{mantenimiento_id}/completar",
    response_model=MantenimientoResponse,
    tags=["Modulo mantenimiento"],
)
def completar_mantenimiento(
    mantenimiento_id: int,
    datos: CompletarMantenimientoRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_admin),
):
    """Cierra un mantenimiento con fecha, costo y kilometraje."""

    return mantenimiento_service.completar_mantenimiento(
        db, mantenimiento_id, datos, usuario.correo
    )


@router.delete("/mantenimientos/{mantenimiento_id}", tags=["Modulo mantenimiento"])
def eliminar_mantenimiento(
    mantenimiento_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_admin),
):
    """Elimina logicamente un mantenimiento (solo administradores)."""

    mantenimiento_service.eliminar_mantenimiento(
        db, mantenimiento_id, usuario.correo
    )
    return {"mensaje": "Mantenimiento eliminado"}


# ---------------------------------------------------------------------------
# Semana 14: preventivos, averias, combustible y costos
# ---------------------------------------------------------------------------


@router.get(
    "/preventivos",
    response_model=List[PreventivoResponse],
    tags=["Modulo mantenimiento"],
)
def listar_preventivos(
    placa: Optional[str] = Query(None, max_length=20),
    categoria: Optional[str] = Query(None, max_length=30),
    limite: int = Query(200, ge=1, le=500),
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_almacen),
):
    """Lista los planes preventivos con su estado calculado."""

    return mantenimiento_service.listar_preventivos(
        db, placa=placa, categoria=categoria, limite=limite
    )


@router.post(
    "/preventivos",
    response_model=PreventivoResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Modulo mantenimiento"],
)
def crear_preventivo(
    datos: PreventivoCreateRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_admin),
):
    """Crea un plan preventivo (solo administradores)."""

    return mantenimiento_service.crear_preventivo(db, datos, usuario.correo)


@router.get(
    "/preventivos/{preventivo_id}",
    response_model=PreventivoResponse,
    tags=["Modulo mantenimiento"],
)
def obtener_preventivo(
    preventivo_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_almacen),
):
    """Devuelve un plan preventivo por su identificador."""

    return mantenimiento_service.obtener_preventivo(db, preventivo_id)


@router.patch(
    "/preventivos/{preventivo_id}",
    response_model=PreventivoResponse,
    tags=["Modulo mantenimiento"],
)
def actualizar_preventivo(
    preventivo_id: int,
    datos: PreventivoUpdateRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_admin),
):
    """Edita un plan preventivo (solo administradores)."""

    return mantenimiento_service.actualizar_preventivo(
        db, preventivo_id, datos, usuario.correo
    )


@router.delete("/preventivos/{preventivo_id}", tags=["Modulo mantenimiento"])
def eliminar_preventivo(
    preventivo_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_admin),
):
    """Da de baja un plan preventivo (solo administradores)."""

    mantenimiento_service.eliminar_preventivo(db, preventivo_id, usuario.correo)
    return {"mensaje": "Plan preventivo eliminado"}


@router.get(
    "/averias/ranking",
    response_model=List[AveriaVehiculoResponse],
    tags=["Modulo mantenimiento"],
)
def ranking_averias(
    limite: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_almacen),
):
    """Ranking de vehiculos con mas averias, leido de incidencias del nucleo."""

    return mantenimiento_service.ranking_averias(db, limite)


@router.get(
    "/combustible",
    response_model=List[CargaCombustibleResponse],
    tags=["Modulo mantenimiento"],
)
def listar_cargas(
    placa: Optional[str] = Query(None, max_length=20),
    tipo: Optional[TipoCombustibleEnum] = Query(None),
    desde: Optional[date] = Query(None),
    hasta: Optional[date] = Query(None),
    limite: int = Query(200, ge=1, le=500),
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_almacen),
):
    """Lista cargas de combustible con rendimiento y consumo anomalo."""

    return mantenimiento_service.listar_cargas(
        db, placa=placa, tipo=tipo, desde=desde, hasta=hasta, limite=limite
    )


@router.post(
    "/combustible",
    response_model=CargaCombustibleResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Modulo mantenimiento"],
)
def crear_carga(
    datos: CargaCombustibleCreateRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_admin),
):
    """Registra una carga de combustible (solo administradores)."""

    return mantenimiento_service.crear_carga(db, datos, usuario.correo)


@router.get(
    "/combustible/{carga_id}",
    response_model=CargaCombustibleResponse,
    tags=["Modulo mantenimiento"],
)
def obtener_carga(
    carga_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_almacen),
):
    """Devuelve una carga de combustible por su identificador."""

    return mantenimiento_service.obtener_carga(db, carga_id)


@router.patch(
    "/combustible/{carga_id}",
    response_model=CargaCombustibleResponse,
    tags=["Modulo mantenimiento"],
)
def actualizar_carga(
    carga_id: int,
    datos: CargaCombustibleUpdateRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_admin),
):
    """Edita una carga de combustible (solo administradores)."""

    return mantenimiento_service.actualizar_carga(db, carga_id, datos, usuario.correo)


@router.delete("/combustible/{carga_id}", tags=["Modulo mantenimiento"])
def eliminar_carga(
    carga_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_admin),
):
    """Da de baja una carga de combustible (solo administradores)."""

    mantenimiento_service.eliminar_carga(db, carga_id, usuario.correo)
    return {"mensaje": "Carga de combustible eliminada"}


@router.get(
    "/costos",
    response_model=CostosFlotaResponse,
    tags=["Modulo mantenimiento"],
)
def obtener_costos(
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_almacen),
):
    """Devuelve costos y rendimiento de toda la flota (mantenimiento + combustible)."""

    return mantenimiento_service.costos_flota(db)


# ---------------------------------------------------------------------------
# Configuracion y auditoria
# ---------------------------------------------------------------------------


@router.get(
    "/configuracion",
    response_model=ConfiguracionResponse,
    tags=["Modulo mantenimiento"],
)
def obtener_configuracion(
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_almacen),
):
    """Devuelve los dias de aviso, la moneda y las banderas de alertas."""

    return mantenimiento_service.configuracion_dict(
        mantenimiento_service.obtener_configuracion(db)
    )


@router.put(
    "/configuracion",
    response_model=ConfiguracionResponse,
    tags=["Modulo mantenimiento"],
)
def actualizar_configuracion(
    datos: ConfiguracionUpdateRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_admin),
):
    """Actualiza la configuracion del modulo (solo administradores)."""

    return mantenimiento_service.actualizar_configuracion(db, datos, usuario.correo)


@router.get(
    "/auditoria",
    response_model=List[AuditoriaResponse],
    tags=["Modulo mantenimiento"],
)
def listar_auditoria(
    limite: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_admin),
):
    """Devuelve los ultimos cambios del modulo (solo administradores)."""

    return mantenimiento_service.historial_auditoria(db, limite)