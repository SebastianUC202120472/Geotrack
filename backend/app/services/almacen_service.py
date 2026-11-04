from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories import almacen_repository, recojo_repository, historial_repository, pedido_repository
from app.schemas.almacen import (
    ConteoConciliacion,
    ConciliacionResponse,
    PedidoIngresoItem,
    RecojoAlmacenItem,
    ConfirmarIngresoResponse,
    ObservadoItem,
)


def estados_ingresables() -> tuple:
    """Estados de recojo que el almacen puede ingresar. Con ALMACEN_INGRESO_DIRECTO (modo
    demostracion) suma SOLICITADO: la solicitud recien aceptada se recibe sin ruta de recojo."""
    if settings.ALMACEN_INGRESO_DIRECTO:
        return ("SOLICITADO", "RECOGIDO", "INGRESADO")
    return ("RECOGIDO", "INGRESADO")


def _recojo_ingresable(db: Session, recojo_id: int, bloquear: bool = False):
    """Devuelve el recojo validando que exista y sea ingresable; bloquear=True usa FOR UPDATE."""
    recojo = (
        recojo_repository.obtener_por_id_bloqueado(db, recojo_id)
        if bloquear
        else recojo_repository.obtener_por_id(db, recojo_id)
    )
    if not recojo:
        raise HTTPException(status_code=404, detail="Recojo no encontrado")
    if recojo.estado not in estados_ingresables():
        raise HTTPException(
            status_code=400,
            detail=f"El recojo debe estar RECOGIDO para ingresarlo (estado: {recojo.estado})",
        )
    return recojo


def _conteo(db: Session, recojo_id: int) -> ConteoConciliacion:
    """Devuelve el conteo de pedidos por estado para un recojo. Recibe id del recojo."""
    total, listos, observados, por_recoger = almacen_repository.contar_pedidos(db, recojo_id)
    return ConteoConciliacion(
        esperados=total,
        listos=listos,
        observados=observados,
        por_recoger=por_recoger,
    )


def obtener_conciliacion(db: Session, recojo_id: int) -> ConciliacionResponse:
    """Devuelve pedidos, fotos y conteo de un recojo para el ingreso manual. Recibe id del recojo."""
    recojo = recojo_repository.obtener_por_id(db, recojo_id)
    if not recojo:
        raise HTTPException(status_code=404, detail="Recojo no encontrado")
    pedidos = almacen_repository.listar_pedidos_recojo(db, recojo_id)
    items = [
        PedidoIngresoItem(
            pedido_id=p.id,
            referencia=p.referencia_externa or "",
            codigo=p.codigo,
            nombre_destinatario=p.nombre_destinatario,
            direccion_destino=p.direccion_destino,
            estado=p.estado,
        )
        for p in pedidos
    ]
    fotos = [e.url_foto for e in almacen_repository.listar_evidencias(db, recojo_id)]
    return ConciliacionResponse(
        recojo_id=recojo_id,
        estado_recojo=recojo.estado,
        conteo=_conteo(db, recojo_id),
        pedidos=items,
        fotos=fotos,
    )


def confirmar_ingreso(db: Session, recojo_id: int, referencias_faltantes: list[str],
                      usuario_id: int | None) -> ConfirmarIngresoResponse:
    """Confirma ingreso manual: faltantes -> OBSERVADO, el resto -> LISTO_PARA_ENVIO, recojo -> INGRESADO. Recibe id recojo, referencias faltantes y usuario."""
    recojo = _recojo_ingresable(db, recojo_id, bloquear=True)
    faltantes = {(r or "").strip() for r in (referencias_faltantes or []) if (r or "").strip()}

    pedidos = almacen_repository.listar_pedidos_recojo(db, recojo_id)
    eventos: list[dict] = []
    ahora = datetime.utcnow()
    for pedido in pedidos:
        es_faltante = (pedido.referencia_externa or "") in faltantes
        if es_faltante:
            if pedido.estado in ("POR_RECOGER", "LISTO_PARA_ENVIO"):
                eventos.append({"pedido_id": pedido.id, "estado_anterior": pedido.estado,
                                "estado_nuevo": "OBSERVADO", "usuario_id": usuario_id})
                pedido.estado = "OBSERVADO"
        elif pedido.estado == "POR_RECOGER":
            eventos.append({"pedido_id": pedido.id, "estado_anterior": pedido.estado,
                            "estado_nuevo": "LISTO_PARA_ENVIO", "usuario_id": usuario_id})
            pedido.estado = "LISTO_PARA_ENVIO"
            pedido.validado_en = ahora
            pedido.validado_por = usuario_id

    historial_repository.registrar_bulk(db, eventos)
    recojo.estado = "INGRESADO"
    almacen_repository.guardar_cambios(db)

    return ConfirmarIngresoResponse(
        recojo_id=recojo_id,
        estado=recojo.estado,
        conteo=_conteo(db, recojo_id),
        mensaje="Ingreso confirmado: pedidos marcados como Listo para envío y faltantes en Observado.",
    )


def listar_recojos(db: Session, estado: str | None = None) -> list:
    """Lista los recojos ingresables (RECOGIDO/INGRESADO, y SOLICITADO en modo demostracion)
    con su conteo de pedidos. Recibe estado opcional para filtrar."""
    estados = [estado] if estado else list(estados_ingresables())
    items = []
    for e in estados:
        for r in recojo_repository.listar(db, e):
            items.append(RecojoAlmacenItem(
                id=r.id,
                codigo=r.codigo,
                cliente_origen=r.cliente_origen,
                estado=r.estado,
                cantidad_declarada=r.cantidad_declarada,
                conteo=_conteo(db, r.id),
            ))
    return items


def listar_observados(db: Session) -> list[ObservadoItem]:
    """Todos los pedidos OBSERVADO con su lote y antigüedad del caso, del mas antiguo al mas nuevo (C15-01). Recibe la sesion."""
    ahora = datetime.utcnow()
    salida = []
    for pedido, lote, desde in pedido_repository.listar_observados(db):
        salida.append(ObservadoItem(
            pedido_id=pedido.id, codigo=pedido.codigo, referencia=pedido.referencia_externa,
            cliente=pedido.cliente_origen, destinatario=pedido.nombre_destinatario,
            direccion_destino=pedido.direccion_destino, lote=lote, recojo_id=pedido.recojo_id,
            observado_desde=desde, dias=max(0, (ahora - desde).days) if desde else 0,
        ))
    return salida
