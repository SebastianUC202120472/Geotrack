# app/services/almacen_service.py
# Lógica del módulo de almacén: ingreso MANUAL de un recojo (sin escaneo). El almacén ve
# las fotos del conductor, marca los pedidos que NO llegaron (quedan OBSERVADO) y confirma
# el ingreso: el resto pasa a LISTO_PARA_ENVIO y el recojo a INGRESADO.
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories import almacen_repository, recojo_repository, historial_repository
from app.schemas.almacen import (
    ConteoConciliacion,
    ConciliacionResponse,
    PedidoIngresoItem,
    RecojoAlmacenItem,
    ConfirmarIngresoResponse,
)

# Un recojo se ingresa cuando ya fue recogido; INGRESADO permite revisarlo de nuevo.
ESTADOS_INGRESABLES = ("RECOGIDO", "INGRESADO")


def _recojo_ingresable(db: Session, recojo_id: int):
    """Devuelve el recojo si existe y está en un estado ingresable; si no, 404/400."""
    recojo = recojo_repository.obtener_por_id(db, recojo_id)
    if not recojo:
        raise HTTPException(status_code=404, detail="Recojo no encontrado")
    if recojo.estado not in ESTADOS_INGRESABLES:
        raise HTTPException(
            status_code=400,
            detail=f"El recojo debe estar RECOGIDO para ingresarlo (estado: {recojo.estado})",
        )
    return recojo


def _conteo(db: Session, recojo_id: int) -> ConteoConciliacion:
    """Arma el resumen de conciliación de un recojo a partir de los estados de sus pedidos."""
    total, listos, observados, por_recoger = almacen_repository.contar_pedidos(db, recojo_id)
    return ConteoConciliacion(
        esperados=total,
        listos=listos,
        observados=observados,
        por_recoger=por_recoger,
    )


def obtener_conciliacion(db: Session, recojo_id: int) -> ConciliacionResponse:
    """Conciliación de un recojo: lista de pedidos (con estado) + fotos de evidencia + conteo.
    Recibe: id del recojo. La usa el panel de almacén para el ingreso manual."""
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
    """Ingreso manual del recojo (sin escaneo): los pedidos cuya referencia esté en
    referencias_faltantes quedan OBSERVADO; el resto (POR_RECOGER) pasa a LISTO_PARA_ENVIO.
    El recojo pasa a INGRESADO. Geocodifica en segundo plano los que falten coordenadas.
    Recibe: id del recojo, lista de referencias (tracking) que NO llegaron y el usuario."""
    _recojo_ingresable(db, recojo_id)
    faltantes = {(r or "").strip() for r in (referencias_faltantes or []) if (r or "").strip()}

    pedidos = almacen_repository.listar_pedidos_recojo(db, recojo_id)
    for pedido in pedidos:
        es_faltante = (pedido.referencia_externa or "") in faltantes
        if es_faltante:
            # Marcar como OBSERVADO (en espera de aclaración) si aún no está resuelto.
            if pedido.estado in ("POR_RECOGER", "LISTO_PARA_ENVIO"):
                historial_repository.registrar(db, pedido.id, pedido.estado, "OBSERVADO", usuario_id)
                pedido.estado = "OBSERVADO"
        elif pedido.estado == "POR_RECOGER":
            # Llegó y no estaba observado: queda listo para envío.
            historial_repository.registrar(db, pedido.id, pedido.estado, "LISTO_PARA_ENVIO", usuario_id)
            pedido.estado = "LISTO_PARA_ENVIO"
            pedido.validado_en = datetime.utcnow()
            pedido.validado_por = usuario_id

    recojo = recojo_repository.obtener_por_id(db, recojo_id)
    recojo.estado = "INGRESADO"
    almacen_repository.guardar_cambios(db)

    # Geocodificar en segundo plano los LISTO_PARA_ENVIO sin coordenadas (no bloquea la respuesta).
    # La tarea la agenda el endpoint (BackgroundTasks); aquí solo devolvemos el resumen.
    return ConfirmarIngresoResponse(
        recojo_id=recojo_id,
        estado=recojo.estado,
        conteo=_conteo(db, recojo_id),
        mensaje="Ingreso confirmado: pedidos marcados como Listo para envío y faltantes en Observado.",
    )


def listar_recojos(db: Session, estado: str | None = None) -> list:
    """Lista los recojos del módulo de almacén (RECOGIDO + INGRESADO) con su conteo desde pedidos."""
    estados = [estado] if estado else ["RECOGIDO", "INGRESADO"]
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
