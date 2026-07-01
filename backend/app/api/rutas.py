from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_current_admin, get_current_conductor
from app.models.usuario import Usuario
from app.services import ruta_service
from app.schemas.ruta import (
    AsignacionBloqueRequest,
    AsignacionBloqueResponse,
    OptimizacionRequest,
    OptimizacionResponse,
    RutaParadasResponse,
    ReordenarRequest,
)

router = APIRouter()


@router.post("/asignar-bloque", response_model=AsignacionBloqueResponse)
def administrador_asigna_bloque(
    asignacion: AsignacionBloqueRequest,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(get_current_admin),
):
    """Asigna un bloque de pedidos de un distrito a un conductor. Recibe AsignacionBloqueRequest."""
    return ruta_service.asignar_bloque(db, asignacion, usuario_id=admin.id)


@router.post("/conductor/optimizar", response_model=OptimizacionResponse)
def conductor_optimiza_ruta(
    solicitud: OptimizacionRequest,
    db: Session = Depends(get_db),
    conductor: Usuario = Depends(get_current_conductor),
):
    """Optimiza la secuencia de la ruta activa del conductor desde su posicion actual. Recibe OptimizacionRequest."""
    return ruta_service.optimizar_ruta(db, solicitud, conductor.id)


@router.get("/{ruta_id}/paradas", response_model=RutaParadasResponse, dependencies=[Depends(get_current_admin)])
def listar_paradas_ruta(ruta_id: int, db: Session = Depends(get_db)):
    """Retorna las paradas ordenadas de una ruta. Recibe ruta_id."""
    return ruta_service.obtener_paradas_admin(db, ruta_id)


@router.patch("/{ruta_id}/reordenar", dependencies=[Depends(get_current_admin)])
def reordenar_paradas(ruta_id: int, datos: ReordenarRequest, db: Session = Depends(get_db)):
    """Reordena las paradas de una ruta. Recibe ruta_id y ReordenarRequest."""
    return ruta_service.reordenar_paradas(db, ruta_id, datos.orden)


@router.delete("/{ruta_id}/paradas/{pedido_id}", dependencies=[Depends(get_current_admin)])
def quitar_parada(ruta_id: int, pedido_id: int, db: Session = Depends(get_db), admin: Usuario = Depends(get_current_admin)):
    """Quita un pedido de la ruta y lo devuelve a LISTO_PARA_ENVIO. Recibe ruta_id y pedido_id."""
    return ruta_service.quitar_parada(db, ruta_id, pedido_id, usuario_id=admin.id)


@router.get("/{ruta_id}/manifiesto", dependencies=[Depends(get_current_admin)])
def descargar_manifiesto(ruta_id: int, db: Session = Depends(get_db)):
    """Genera y descarga el manifiesto de carga de una ruta en Excel. Recibe ruta_id."""
    contenido, nombre = ruta_service.generar_manifiesto_excel(db, ruta_id)
    return Response(
        content=contenido,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{nombre}"'},
    )
