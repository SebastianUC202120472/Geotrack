import os
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.ruta import Ruta, RutaDetalle
from app.models.pedido import Pedido
from app.repositories import ruta_repository, pedido_repository, historial_repository, evidencia_repository, incidencia_repository, recojo_repository
from app.services.router import optimizar_secuencia_pedidos, distancia_total
from app.schemas.ruta import (
    RutaActivaResponse,
    ManifiestoResponse,
    ParadaManifiesto,
    NavegacionResponse,
    ParadaNavegacion,
    GestionParadaResponse,
    CierreRutaResponse,
    AsignacionBloqueRequest,
    OptimizacionRequest,
)

# Directorio de fotos POD, servido en /media.
DIR_EVIDENCIAS = os.path.join("uploads", "evidencias")
EXTENSIONES_IMAGEN = {".jpg", ".jpeg", ".png", ".webp"}


def _construir_parada(detalle: RutaDetalle, pedido: Pedido) -> ParadaManifiesto:
    return ParadaManifiesto(
        secuencia=detalle.secuencia,
        detalle_id=detalle.id,
        pedido_id=pedido.id,
        codigo=pedido.codigo,
        cliente_origen=pedido.cliente_origen,
        nombre_destinatario=pedido.nombre_destinatario,
        telefono_destinatario=pedido.telefono_destinatario,
        direccion_destino=pedido.direccion_destino,
        distrito=pedido.distrito,
        latitud=pedido.latitud,
        longitud=pedido.longitud,
        peso_kg=pedido.peso_kg,
        estado_entrega=detalle.estado_entrega,
        url_evidencia=detalle.url_evidencia,
    )


def _obtener_ruta_activa_o_404(db: Session, conductor_id: int) -> Ruta:
    ruta = ruta_repository.obtener_ruta_activa_por_conductor(db, conductor_id)
    if not ruta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No tienes una ruta activa asignada",
        )
    return ruta


def obtener_resumen_ruta_activa(db: Session, conductor_id: int) -> RutaActivaResponse:
    """Resumen de la ruta activa con contadores de avance. Recibe: id del conductor."""
    ruta = _obtener_ruta_activa_o_404(db, conductor_id)
    abierta = incidencia_repository.obtener_abierta_por_ruta(db, ruta.id)

    if ruta.tipo == "RECOJO":
        recojos = recojo_repository.obtener_por_ruta(db, ruta.id)
        total = len(recojos)
        recogidas = sum(1 for r in recojos if r.estado == "RECOGIDO")
        return RutaActivaResponse(
            ruta_id=ruta.id, codigo=ruta.codigo, nombre=ruta.nombre, estado=ruta.estado,
            fecha_creacion=ruta.fecha_creacion, fecha_salida=ruta.fecha_salida,
            vehiculo_placa=ruta.vehiculo_placa, total_paradas=total, pendientes=total - recogidas,
            entregadas=recogidas, fallidas=0, pausada=abierta is not None,
            incidencia_id=abierta.id if abierta else None,
            ayuda_enviada_en=abierta.ayuda_enviada_en if abierta else None,
            ayuda_detalle=abierta.ayuda_detalle if abierta else None, tipo=ruta.tipo,
        )

    detalles = ruta_repository.obtener_detalles_con_pedido(db, ruta.id)
    pendientes = sum(1 for d, _ in detalles if d.estado_entrega == "PENDIENTE")
    entregadas = sum(1 for d, _ in detalles if d.estado_entrega == "ENTREGADO")
    fallidas = sum(1 for d, _ in detalles if d.estado_entrega == "FALLIDO")

    return RutaActivaResponse(
        ruta_id=ruta.id, codigo=ruta.codigo, nombre=ruta.nombre, estado=ruta.estado,
        fecha_creacion=ruta.fecha_creacion, fecha_salida=ruta.fecha_salida,
        vehiculo_placa=ruta.vehiculo_placa, total_paradas=len(detalles), pendientes=pendientes,
        entregadas=entregadas, fallidas=fallidas, pausada=abierta is not None,
        incidencia_id=abierta.id if abierta else None,
        ayuda_enviada_en=abierta.ayuda_enviada_en if abierta else None,
        ayuda_detalle=abierta.ayuda_detalle if abierta else None, tipo=ruta.tipo,
    )


def obtener_manifiesto(db: Session, conductor_id: int) -> ManifiestoResponse:
    """Manifiesto detallado ordenado por secuencia. Recibe: id del conductor."""
    ruta = _obtener_ruta_activa_o_404(db, conductor_id)
    detalles = ruta_repository.obtener_detalles_con_pedido(db, ruta.id)

    paradas = [_construir_parada(detalle, pedido) for detalle, pedido in detalles]

    return ManifiestoResponse(
        ruta_id=ruta.id,
        codigo=ruta.codigo,
        nombre=ruta.nombre,
        estado=ruta.estado,
        total_paradas=len(paradas),
        paradas=paradas,
    )


def obtener_navegacion(db: Session, conductor_id: int) -> NavegacionResponse:
    """Waypoints lat/lng ordenados para el mapa de la app. Recibe: id del conductor."""
    ruta = _obtener_ruta_activa_o_404(db, conductor_id)
    detalles = ruta_repository.obtener_detalles_con_pedido(db, ruta.id)

    paradas = [
        ParadaNavegacion(
            secuencia=detalle.secuencia,
            pedido_id=pedido.id,
            codigo=pedido.codigo,
            latitud=pedido.latitud,
            longitud=pedido.longitud,
        )
        for detalle, pedido in detalles
        if pedido.latitud is not None and pedido.longitud is not None
    ]

    return NavegacionResponse(
        ruta_id=ruta.id,
        total_paradas=len(paradas),
        paradas=paradas,
    )


def _obtener_detalle_de_mi_ruta(
    db: Session, conductor_id: int, pedido_id: int
) -> RutaDetalle:
    """Devuelve el detalle del pedido validando que pertenece a la ruta activa del conductor."""
    ruta = _obtener_ruta_activa_o_404(db, conductor_id)
    detalle = ruta_repository.obtener_detalle_de_ruta(db, ruta.id, pedido_id)
    if not detalle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Este pedido no pertenece a tu ruta activa",
        )
    return detalle


def actualizar_estado_parada(
    db: Session,
    conductor_id: int,
    pedido_id: int,
    estado: str,
    motivo_fallo: str | None,
) -> GestionParadaResponse:
    """Marca un pedido como ENTREGADO o FALLIDO. Recibe: id del conductor, pedido, estado y motivo."""
    if estado == "FALLIDO" and not (motivo_fallo and motivo_fallo.strip()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debes indicar el motivo del fallo en una entrega fallida",
        )

    detalle = _obtener_detalle_de_mi_ruta(db, conductor_id, pedido_id)

    if incidencia_repository.tiene_abierta(db, detalle.ruta_id):
        raise HTTPException(status_code=400, detail="La ruta está pausada por una incidencia. Reanúdala antes de continuar.")

    # Exige foto POD antes de marcar ENTREGADO.
    if estado == "ENTREGADO" and not detalle.url_evidencia:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Adjunta la foto de evidencia (POD) antes de marcar la entrega como ENTREGADO.",
        )

    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()

    ahora = datetime.utcnow()
    estado_anterior = pedido.estado
    detalle.estado_entrega = estado
    detalle.fecha_gestion = ahora
    detalle.motivo_fallo = motivo_fallo if estado == "FALLIDO" else None

    pedido.estado = estado
    pedido.fecha_entrega = ahora if estado == "ENTREGADO" else None

    if detalle.ruta and detalle.ruta.estado == "CREADA":
        detalle.ruta.estado = "EN_PROGRESO"

    historial_repository.registrar(db, pedido.id, estado_anterior, estado, conductor_id)

    db.commit()
    db.refresh(detalle)

    return GestionParadaResponse(
        pedido_id=pedido.id,
        codigo=pedido.codigo,
        estado_entrega=detalle.estado_entrega,
        motivo_fallo=detalle.motivo_fallo,
        url_evidencia=detalle.url_evidencia,
        fecha_gestion=detalle.fecha_gestion,
        mensaje=f"Pedido marcado como {estado}",
    )


def guardar_evidencia(
    db: Session,
    conductor_id: int,
    pedido_id: int,
    contenido: bytes,
    nombre_archivo: str,
) -> GestionParadaResponse:
    """Guarda la foto POD y la asocia al detalle de ruta. Recibe: id conductor, pedido, bytes e imagen."""
    detalle = _obtener_detalle_de_mi_ruta(db, conductor_id, pedido_id)

    _, extension = os.path.splitext(nombre_archivo.lower())
    if extension not in EXTENSIONES_IMAGEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato no permitido. Usa: {', '.join(sorted(EXTENSIONES_IMAGEN))}",
        )

    os.makedirs(DIR_EVIDENCIAS, exist_ok=True)
    nombre_final = f"pod_{detalle.ruta_id}_{pedido_id}{extension}"
    ruta_fisica = os.path.join(DIR_EVIDENCIAS, nombre_final)
    with open(ruta_fisica, "wb") as f:
        f.write(contenido)

    url = f"/media/evidencias/{nombre_final}"
    detalle.url_evidencia = url
    db.commit()
    db.refresh(detalle)

    evidencia_repository.registrar_foto(db, pedido_id, url)

    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    return GestionParadaResponse(
        pedido_id=pedido.id,
        codigo=pedido.codigo,
        estado_entrega=detalle.estado_entrega,
        motivo_fallo=detalle.motivo_fallo,
        url_evidencia=detalle.url_evidencia,
        fecha_gestion=detalle.fecha_gestion,
        mensaje="Evidencia (POD) cargada correctamente",
    )


def finalizar_ruta(db: Session, conductor_id: int) -> CierreRutaResponse:
    """Da por finalizada la ruta activa del conductor. Recibe: id del conductor."""
    ruta = _obtener_ruta_activa_o_404(db, conductor_id)

    if ruta.tipo == "RECOJO":
        from app.services import recojo_service  # import local: evita ciclo de imports
        return recojo_service.finalizar_ruta_recojo(db, ruta)

    if incidencia_repository.tiene_abierta(db, ruta.id):
        raise HTTPException(status_code=400, detail="La ruta está pausada por una incidencia. Reanúdala antes de cerrar el día.")

    detalles = ruta_repository.obtener_detalles_con_pedido(db, ruta.id)

    pendientes = sum(1 for d, _ in detalles if d.estado_entrega == "PENDIENTE")
    entregadas = sum(1 for d, _ in detalles if d.estado_entrega == "ENTREGADO")
    fallidas = sum(1 for d, _ in detalles if d.estado_entrega == "FALLIDO")

    if pendientes:
        raise HTTPException(
            status_code=400,
            detail=f"No puedes cerrar la ruta: quedan {pendientes} parada(s) pendiente(s) por gestionar.",
        )

    ruta.estado = "FINALIZADA"
    ruta.fecha_fin = datetime.utcnow()

    # Estima km si la ruta nunca se optimizó.
    if ruta.km_estimado is None and detalles:
        pedidos_ordenados = [pedido for _, pedido in detalles]
        primero = next((p for p in pedidos_ordenados if p.latitud is not None and p.longitud is not None), None)
        if primero is not None:
            ruta.km_estimado = round(distancia_total(primero.latitud, primero.longitud, pedidos_ordenados), 2)
            ruta.km_ahorrado = 0.0

    hora_inicio = ruta.fecha_salida or ruta.fecha_creacion
    duracion_minutos = None
    if hora_inicio:
        duracion_minutos = max(0, int((ruta.fecha_fin - hora_inicio).total_seconds() // 60))

    db.commit()

    mensaje = "Ruta finalizada correctamente"

    return CierreRutaResponse(
        ruta_id=ruta.id,
        codigo=ruta.codigo,
        nombre=ruta.nombre,
        estado=ruta.estado,
        fecha_fin=ruta.fecha_fin,
        hora_inicio=hora_inicio,
        hora_fin=ruta.fecha_fin,
        duracion_minutos=duracion_minutos,
        total_paradas=len(detalles),
        entregadas=entregadas,
        fallidas=fallidas,
        pendientes=pendientes,
        mensaje=mensaje,
    )


def asignar_bloque(db: Session, datos: AsignacionBloqueRequest, usuario_id: int | None = None) -> dict:
    """Crea una ruta con todos los pedidos LISTO_PARA_ENVIO de un distrito. Recibe: datos de asignacion e id del admin."""
    pedidos = pedido_repository.obtener_pendientes_por_distrito(db, datos.distrito)
    if not pedidos:
        raise HTTPException(status_code=400, detail="No hay pedidos pendientes para esa zona")

    if datos.conductor_id:
        activa = ruta_repository.obtener_ruta_activa_por_conductor(db, datos.conductor_id)
        if activa:
            raise HTTPException(
                status_code=400,
                detail=f"El conductor ya tiene una ruta activa ('{activa.nombre}'). Debe cerrarla antes de asignar otra.",
            )

    nombre = (datos.nombre_ruta or "").strip() or f"Ruta {datos.distrito or 'sin zona'}"

    ruta = ruta_repository.crear_ruta(db, nombre=nombre, conductor_id=datos.conductor_id)

    for pedido in pedidos:
        ruta_repository.agregar_detalle(db, ruta_id=ruta.id, pedido_id=pedido.id, secuencia=0)
        estado_anterior = pedido.estado
        pedido.estado = "ASIGNADO"
        historial_repository.registrar(db, pedido.id, estado_anterior, "ASIGNADO", usuario_id)

    ruta_repository.guardar_cambios(db)

    return {
        "mensaje": f"{len(pedidos)} pedidos asignados a la ruta '{nombre}'",
        "ruta_id": ruta.id,
        "codigo": ruta.codigo,
    }


def optimizar_ruta(db: Session, datos: OptimizacionRequest, conductor_id: int) -> dict:
    """Optimiza el orden de entrega de la ruta del conductor (vecino mas cercano). Recibe: datos de posicion e id del conductor."""
    ruta = ruta_repository.obtener_ruta_por_id(db, datos.ruta_id)
    if not ruta:
        raise HTTPException(status_code=404, detail="Ruta no encontrada")

    if ruta.conductor_id != conductor_id:
        raise HTTPException(status_code=403, detail="Esta ruta no está asignada a tu usuario")

    detalles = ruta_repository.obtener_detalles_con_pedido(db, ruta.id)
    detalle_por_pedido = {pedido.id: detalle for detalle, pedido in detalles}
    pedidos_validos = [pedido for _, pedido in detalles if pedido.latitud is not None]
    if not pedidos_validos:
        raise HTTPException(status_code=400, detail="La ruta no tiene pedidos válidos para optimizar")

    ordenados = optimizar_secuencia_pedidos(
        pedidos_validos,
        datos.latitud_actual_conductor,
        datos.longitud_actual_conductor,
    )

    origen = (datos.latitud_actual_conductor, datos.longitud_actual_conductor)
    km_base = distancia_total(origen[0], origen[1], pedidos_validos)
    km_opt = distancia_total(origen[0], origen[1], ordenados)
    ruta.km_estimado = round(km_opt, 2)
    ruta.km_ahorrado = round(max(0.0, km_base - km_opt), 2)

    secuencia = 1
    eventos: list[dict] = []
    for pedido in ordenados:
        detalle = detalle_por_pedido.get(pedido.id)
        if detalle is not None:
            detalle.secuencia = secuencia
        estado_anterior = pedido.estado
        pedido.estado = "EN_RUTA"
        eventos.append({"pedido_id": pedido.id, "estado_anterior": estado_anterior,
                        "estado_nuevo": "EN_RUTA", "usuario_id": conductor_id})
        secuencia += 1
    historial_repository.registrar_bulk(db, eventos)

    # Sella la salida la primera vez que el conductor optimiza.
    if ruta.fecha_salida is None:
        ruta.fecha_salida = datetime.utcnow()
        ruta.estado = "EN_PROGRESO"

    ruta_repository.guardar_cambios(db)

    return {"mensaje": "Ruta optimizada matemáticamente", "total_paradas": len(ordenados)}


def _ruta_o_404(db: Session, ruta_id: int) -> Ruta:
    """Devuelve la ruta o lanza 404. Recibe: id de ruta."""
    ruta = ruta_repository.obtener_ruta_por_id(db, ruta_id)
    if not ruta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ruta no encontrada")
    return ruta


def _ruta_editable_o_400(db: Session, ruta_id: int) -> Ruta:
    """Devuelve la ruta si es editable; lanza 400 si ya esta FINALIZADA. Recibe: id de ruta."""
    ruta = _ruta_o_404(db, ruta_id)
    if ruta.estado == "FINALIZADA":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="La ruta ya está finalizada; no se pueden editar sus paradas.")
    return ruta


def obtener_paradas_admin(db: Session, ruta_id: int):
    """Paradas ordenadas de una ruta para edicion en el panel. Recibe: id de ruta."""
    ruta = _ruta_o_404(db, ruta_id)
    detalles = ruta_repository.obtener_detalles_con_pedido(db, ruta.id)
    paradas = [
        {
            "secuencia": detalle.secuencia,
            "pedido_id": pedido.id,
            "codigo": pedido.codigo,
            "cliente_origen": pedido.cliente_origen,
            "nombre_destinatario": pedido.nombre_destinatario,
            "direccion_destino": pedido.direccion_destino,
            "distrito": pedido.distrito,
            "estado_entrega": detalle.estado_entrega,
        }
        for detalle, pedido in detalles
    ]
    return {
        "ruta_id": ruta.id, "codigo": ruta.codigo, "nombre": ruta.nombre,
        "estado": ruta.estado, "total_paradas": len(paradas), "paradas": paradas,
    }


def reordenar_paradas(db: Session, ruta_id: int, orden: list[int]) -> dict:
    """Reescribe la secuencia de paradas segun la lista de pedido_id recibida. Recibe: id de ruta y lista ordenada."""
    ruta = _ruta_editable_o_400(db, ruta_id)
    secuencia = 1
    vistos = set()
    for pedido_id in orden:
        detalle = ruta_repository.obtener_detalle_de_ruta(db, ruta.id, pedido_id)
        if detalle:
            detalle.secuencia = secuencia
            secuencia += 1
            vistos.add(pedido_id)
    # Paradas no incluidas en el orden recibido van al final.
    for detalle, pedido in ruta_repository.obtener_detalles_con_pedido(db, ruta.id):
        if pedido.id not in vistos:
            detalle.secuencia = secuencia
            secuencia += 1
    db.commit()
    return {"mensaje": "Orden de paradas actualizado", "total_paradas": secuencia - 1}


def quitar_parada(db: Session, ruta_id: int, pedido_id: int, usuario_id: int | None = None) -> dict:
    """Quita un pedido de la ruta y lo devuelve a LISTO_PARA_ENVIO. Recibe: id de ruta, pedido y admin."""
    ruta = _ruta_editable_o_400(db, ruta_id)
    detalle = ruta_repository.obtener_detalle_de_ruta(db, ruta.id, pedido_id)
    if not detalle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Esa parada no pertenece a la ruta")
    if detalle.estado_entrega in ("ENTREGADO", "FALLIDO"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="No se puede quitar una parada ya gestionada (entregada o fallida).")

    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    db.delete(detalle)
    if pedido:
        estado_anterior = pedido.estado
        pedido.estado = "LISTO_PARA_ENVIO"
        pedido.fecha_entrega = None
        historial_repository.registrar(db, pedido.id, estado_anterior, "LISTO_PARA_ENVIO", usuario_id)
    db.commit()
    return {"mensaje": "Parada quitada de la ruta; el pedido volvió a Listo para envío"}


COLUMNAS_MANIFIESTO = ["Secuencia", "Código", "Cliente", "Destinatario", "Dirección", "Distrito", "Teléfono", "Estado"]


def generar_manifiesto_excel(db: Session, ruta_id: int) -> tuple[bytes, str]:
    """Genera el manifiesto de carga como Excel en memoria. Recibe: id de ruta. Devuelve: (bytes, nombre)."""
    import io
    from openpyxl import Workbook
    from openpyxl.styles import Font

    ruta = _ruta_o_404(db, ruta_id)
    detalles = ruta_repository.obtener_detalles_con_pedido(db, ruta.id)

    wb = Workbook()
    hoja = wb.active
    hoja.title = "Manifiesto"
    hoja.append([f"Manifiesto de carga · {ruta.nombre} ({ruta.codigo or ruta.id})"])
    hoja.append(COLUMNAS_MANIFIESTO)
    for celda in hoja[2]:
        celda.font = Font(bold=True)

    for detalle, pedido in detalles:
        hoja.append([
            detalle.secuencia,
            pedido.codigo or "",
            pedido.cliente_origen or "",
            pedido.nombre_destinatario or "",
            pedido.direccion_destino or "",
            pedido.distrito or "",
            pedido.telefono_destinatario or "",
            detalle.estado_entrega or "",
        ])

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    nombre = f"manifiesto_{ruta.codigo or ruta.id}.xlsx"
    return buffer.getvalue(), nombre
