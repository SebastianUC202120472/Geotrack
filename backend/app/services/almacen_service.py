# app/services/almacen_service.py
# Lógica del módulo de almacén (CUS-14): escanear pedidos del recojo,
# conciliar y cerrar el ingreso.
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories import almacen_repository, recojo_repository
from app.services import geocoder
from app.schemas.almacen import (
    ConteoConciliacion,
    EscaneoResponse,
    ConciliacionResponse,
    PaqueteEsperadoItem,
    RecojoAlmacenItem,
    CerrarIngresoResponse,
)

# Un recojo se ingresa cuando ya fue recogido; INGRESADO permite reabrir/reescanear.
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
    """Arma el resumen de conciliación de un recojo a partir de sus pedidos."""
    total, validados, faltantes = almacen_repository.contar_pedidos(db, recojo_id)
    desconocidos = almacen_repository.contar_desconocidos(db, recojo_id)
    return ConteoConciliacion(
        esperados=total,
        ingresados=validados,
        faltantes=faltantes,
        desconocidos=desconocidos,
    )


def escanear(db: Session, recojo_id: int, codigo: str, usuario_id: int | None) -> EscaneoResponse:
    """Cruza un código escaneado contra los pedidos del recojo por referencia_externa.
    Recibe: id de recojo, tracking del cliente escaneado y usuario."""
    _recojo_ingresable(db, recojo_id)
    codigo = (codigo or "").strip()
    if not codigo:
        raise HTTPException(status_code=400, detail="El código no puede estar vacío")

    pedido = almacen_repository.obtener_pedido_por_tracking(db, recojo_id, codigo)

    if pedido is None:
        # El tracking no pertenece a ningún pedido de este recojo.
        if not almacen_repository.obtener_desconocido(db, recojo_id, codigo):
            almacen_repository.agregar_desconocido(db, recojo_id, codigo, usuario_id)
            almacen_repository.guardar_cambios(db)
        return EscaneoResponse(
            resultado="DESCONOCIDO",
            codigo=codigo,
            mensaje="El código no corresponde a ningún pedido de este recojo",
            conteo=_conteo(db, recojo_id),
        )

    if pedido.estado != "POR_RECOGER":
        # Ya fue validado antes; no re-aplicar.
        return EscaneoResponse(
            resultado="DUPLICADO",
            codigo=codigo,
            mensaje="Este pedido ya fue ingresado",
            conteo=_conteo(db, recojo_id),
        )

    # Primera validación: pasa a PENDIENTE (entregable).
    pedido.estado = "PENDIENTE"
    pedido.validado_en = datetime.utcnow()
    pedido.validado_por = usuario_id

    # Si no tiene coordenadas, intentar geocodificar la dirección destino.
    if pedido.latitud is None or pedido.longitud is None:
        lat, lng = geocoder.obtener_coordenadas(pedido.direccion_destino)
        if lat is not None:
            pedido.latitud = lat
            pedido.longitud = lng
            # Extraer el distrito: texto tras la primera coma de la dirección.
            partes = pedido.direccion_destino.split(",", 1)
            if len(partes) > 1:
                pedido.distrito = partes[1].strip()

    almacen_repository.guardar_cambios(db)
    return EscaneoResponse(
        resultado="INGRESADO",
        codigo=codigo,
        mensaje="Pedido validado e ingresado correctamente",
        conteo=_conteo(db, recojo_id),
    )


def obtener_conciliacion(db: Session, recojo_id: int) -> ConciliacionResponse:
    """Conciliación detallada de un recojo: pedidos (tracking + estado) + desconocidos + conteo."""
    recojo = recojo_repository.obtener_por_id(db, recojo_id)
    if not recojo:
        raise HTTPException(status_code=404, detail="Recojo no encontrado")
    pedidos = almacen_repository.listar_pedidos_recojo(db, recojo_id)
    esperados = [
        PaqueteEsperadoItem(
            codigo=p.referencia_externa or p.codigo or "",
            estado=p.estado,
            escaneado_en=p.validado_en,
        )
        for p in pedidos
    ]
    desconocidos = [d.codigo for d in almacen_repository.listar_desconocidos(db, recojo_id)]
    return ConciliacionResponse(
        recojo_id=recojo_id,
        estado_recojo=recojo.estado,
        conteo=_conteo(db, recojo_id),
        esperados=esperados,
        desconocidos=desconocidos,
    )


def cerrar_ingreso(db: Session, recojo_id: int, usuario_id: int | None) -> CerrarIngresoResponse:
    """Cierra el ingreso: el recojo pasa a INGRESADO (permitido aun con faltantes)."""
    recojo = _recojo_ingresable(db, recojo_id)
    recojo.estado = "INGRESADO"
    almacen_repository.guardar_cambios(db)
    return CerrarIngresoResponse(
        recojo_id=recojo_id,
        estado=recojo.estado,
        conteo=_conteo(db, recojo_id),
        mensaje="Ingreso cerrado",
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
