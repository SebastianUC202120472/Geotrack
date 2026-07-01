# Logica de retorno: recepcion y conciliacion de paquetes FALLIDO devueltos por el conductor.
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories import ruta_repository
from app.schemas.almacen import (
    ConteoRetorno,
    RutaRetornoItem,
    FallidoItem,
    RetornoRutaResponse,
    EscaneoRetornoResponse,
)


def _conteo(db: Session, ruta_id: int) -> ConteoRetorno:
    """Arma el resumen de retorno de una ruta."""
    esperados, retornados = ruta_repository.contar_retorno(db, ruta_id)
    return ConteoRetorno(esperados=esperados, retornados=retornados, faltantes=esperados - retornados)


def listar_rutas(db: Session) -> list:
    """Rutas de entrega con paquetes FALLIDO (candidatas a retorno), con su conteo."""
    items = []
    for ruta in ruta_repository.obtener_rutas_con_fallidos(db):
        items.append(RutaRetornoItem(
            ruta_id=ruta.id, codigo=ruta.codigo, nombre=ruta.nombre, estado=ruta.estado,
            conteo=_conteo(db, ruta.id),
        ))
    return items


def obtener_retorno(db: Session, ruta_id: int) -> RetornoRutaResponse:
    """Detalle del retorno de una ruta: sus FALLIDO con estado de retorno + conteo."""
    ruta = ruta_repository.obtener_ruta_por_id(db, ruta_id)
    if not ruta:
        raise HTTPException(status_code=404, detail="Ruta no encontrada")
    fallidos = [
        FallidoItem(
            pedido_id=pedido.id, codigo=pedido.codigo, cliente_origen=pedido.cliente_origen,
            direccion_destino=pedido.direccion_destino, nombre_destinatario=pedido.nombre_destinatario,
            retornado_en=detalle.retornado_en,
        )
        for detalle, pedido in ruta_repository.obtener_fallidos_de_ruta(db, ruta_id)
    ]
    return RetornoRutaResponse(
        ruta_id=ruta.id, codigo=ruta.codigo, nombre=ruta.nombre,
        conteo=_conteo(db, ruta_id), fallidos=fallidos,
    )


def escanear(db: Session, ruta_id: int, codigo: str, usuario_id: int | None) -> EscaneoRetornoResponse:
    """Cruza un código devuelto contra los FALLIDO de la ruta y marca el retorno."""
    ruta = ruta_repository.obtener_ruta_por_id(db, ruta_id)
    if not ruta:
        raise HTTPException(status_code=404, detail="Ruta no encontrada")
    codigo = (codigo or "").strip()
    if not codigo:
        raise HTTPException(status_code=400, detail="El código no puede estar vacío")

    detalle = ruta_repository.obtener_fallido_por_codigo(db, ruta_id, codigo)
    if detalle is None:
        return EscaneoRetornoResponse(resultado="DESCONOCIDO", codigo=codigo, mensaje="El código no es un paquete fallido de esta ruta", conteo=_conteo(db, ruta_id))
    if detalle.retornado_en is not None:
        return EscaneoRetornoResponse(resultado="DUPLICADO", codigo=codigo, mensaje="Este paquete ya fue registrado como retornado", conteo=_conteo(db, ruta_id))

    detalle.retornado_en = datetime.utcnow()
    detalle.retornado_por = usuario_id
    ruta_repository.guardar_cambios(db)
    return EscaneoRetornoResponse(resultado="RETORNADO", codigo=codigo, mensaje="Paquete retornado correctamente", conteo=_conteo(db, ruta_id))
