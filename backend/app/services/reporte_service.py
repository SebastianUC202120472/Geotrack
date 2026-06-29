# app/services/reporte_service.py
# Lógica de los reportes de incidencia: el conductor crea uno cuando un pedido
# falla y el admin lo responde con una solución.
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories import reporte_repository, conductor_repository
from app.models.pedido import Pedido
from app.models.conductor import PerfilConductor
from app.schemas.reporte import ReporteCreate, ResponderReporte
from app.services import notificaciones_service


def _a_respuesta(db: Session, r) -> dict:
    """Arma la respuesta del reporte con la dirección del pedido y el nombre del conductor."""
    pedido = db.query(Pedido).filter(Pedido.id == r.pedido_id).first()
    perfil = db.query(PerfilConductor).filter(PerfilConductor.usuario_id == r.conductor_id).first()
    return {
        "id": r.id,
        "pedido_id": r.pedido_id,
        "pedido_codigo": r.pedido_codigo,
        "direccion_destino": pedido.direccion_destino if pedido else None,
        "conductor_id": r.conductor_id,
        "conductor_nombre": perfil.nombre if perfil else None,
        "motivo": r.motivo,
        "descripcion": r.descripcion,
        "estado": r.estado,
        "respuesta": r.respuesta,
        "accion": r.accion,
        "creado_en": r.creado_en,
        "respondido_en": r.respondido_en,
    }


def crear(db: Session, conductor_id: int, datos: ReporteCreate) -> dict:
    """CONDUCTOR: crea un reporte para un pedido. Guarda el código del pedido como snapshot."""
    if not datos.motivo.strip():
        raise HTTPException(status_code=400, detail="Indica el motivo de la falla")
    pedido = db.query(Pedido).filter(Pedido.id == datos.pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    reporte = reporte_repository.crear(
        db,
        pedido_id=datos.pedido_id,
        pedido_codigo=pedido.codigo,
        conductor_id=conductor_id,
        motivo=datos.motivo.strip(),
        descripcion=(datos.descripcion or None),
    )
    # Notifica al admin que llegó un reporte de entrega fallida.
    try:
        notificaciones_service.registrar(
            db, "reportes", "Nuevo reporte de entrega",
            f"Pedido {pedido.codigo}: {datos.motivo.strip()}", "/reportes?pendientes=1", reporte.id)
    except Exception:
        pass
    return _a_respuesta(db, reporte)


def listar(db: Session, estado: str | None = None) -> list:
    """ADMIN: lista los reportes (abiertos primero)."""
    return [_a_respuesta(db, r) for r in reporte_repository.listar(db, estado)]


def listar_mios(db: Session, conductor_id: int) -> list:
    """CONDUCTOR: sus propios reportes (para ver la respuesta del admin)."""
    return [_a_respuesta(db, r) for r in reporte_repository.listar_por_conductor(db, conductor_id)]


def responder(db: Session, reporte_id: int, admin_id: int, datos: ResponderReporte) -> dict:
    """ADMIN: responde un reporte con la solución y lo marca resuelto."""
    reporte = reporte_repository.obtener(db, reporte_id)
    if not reporte:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    if not datos.respuesta.strip():
        raise HTTPException(status_code=400, detail="Escribe una respuesta")
    reporte.respuesta = datos.respuesta.strip()
    reporte.accion = datos.accion
    reporte.estado = (datos.estado or "RESUELTO").upper()
    reporte.respondido_en = datetime.utcnow()
    reporte.respondido_por = admin_id
    reporte_repository.guardar(db)
    return _a_respuesta(db, reporte)
