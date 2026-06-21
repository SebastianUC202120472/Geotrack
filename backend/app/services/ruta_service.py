# app/services/ruta_service.py
# Reúne la lógica de RUTAS en dos momentos del MVP.
import os
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.ruta import Ruta, RutaDetalle
from app.models.pedido import Pedido
from app.repositories import ruta_repository, pedido_repository, historial_repository, evidencia_repository, incidencia_repository
from app.services.router import optimizar_secuencia_pedidos
from app.schemas.ruta import (
    RutaActivaResponse,
    ManifiestoResponse,
    ParadaManifiesto,
    NavegacionResponse,
    ParadaNavegacion,
    ValidacionQRResponse,
    GestionParadaResponse,
    CierreRutaResponse,
    AsignacionBloqueRequest,
    OptimizacionRequest,
)

# Carpeta donde se guardan las fotos POD (CUS-29). Servida en /media.
DIR_EVIDENCIAS = os.path.join("uploads", "evidencias")
EXTENSIONES_IMAGEN = {".jpg", ".jpeg", ".png", ".webp"}


def _construir_parada(detalle: RutaDetalle, pedido: Pedido) -> ParadaManifiesto:
    return ParadaManifiesto(
        secuencia=detalle.secuencia,
        detalle_id=detalle.id,
        pedido_id=pedido.id,
        codigo=pedido.codigo,
        cliente_origen=pedido.cliente_origen,
        # Datos del destinatario: el conductor necesita saber a QUIÉN entrega.
        nombre_destinatario=pedido.nombre_destinatario,
        telefono_destinatario=pedido.telefono_destinatario,
        direccion_destino=pedido.direccion_destino,
        distrito=pedido.distrito,
        latitud=pedido.latitud,
        longitud=pedido.longitud,
        peso_kg=pedido.peso_kg,
        estado_entrega=detalle.estado_entrega,
        # Se expone la URL guardada en BD para que la App muestre la foto POD ya subida
        # (antes la App dependía de un caché en memoria que se perdía al cerrarse).
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
    """CUS-21: resumen de la ruta activa con contadores de avance."""
    ruta = _obtener_ruta_activa_o_404(db, conductor_id)
    detalles = ruta_repository.obtener_detalles_con_pedido(db, ruta.id)

    pendientes = sum(1 for d, _ in detalles if d.estado_entrega == "PENDIENTE")
    entregadas = sum(1 for d, _ in detalles if d.estado_entrega == "ENTREGADO")
    fallidas = sum(1 for d, _ in detalles if d.estado_entrega == "FALLIDO")

    # CUS-30: comprueba si existe una incidencia abierta (auxilio mecánico) para esta ruta.
    abierta = incidencia_repository.obtener_abierta_por_ruta(db, ruta.id)

    return RutaActivaResponse(
        ruta_id=ruta.id,
        codigo=ruta.codigo,
        nombre=ruta.nombre,
        estado=ruta.estado,
        fecha_creacion=ruta.fecha_creacion,
        fecha_salida=ruta.fecha_salida,  # CUS-23: sello de salida (la App muestra "Salida HH:MM")
        vehiculo_placa=ruta.vehiculo_placa,
        total_paradas=len(detalles),
        pendientes=pendientes,
        entregadas=entregadas,
        fallidas=fallidas,
        pausada=abierta is not None,
        incidencia_id=abierta.id if abierta else None,
    )


def obtener_manifiesto(db: Session, conductor_id: int) -> ManifiestoResponse:
    """CUS-24: manifiesto detallado y ordenado por secuencia de entrega."""
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
    """CUS-25: waypoints (lat/lng) ordenados para alimentar el mapa de la App."""
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


# FASE 3.2: Validación en almacén (CUS-22)
def validar_paquete_qr(
    db: Session, conductor_id: int, codigo: str
) -> ValidacionQRResponse:
    """Verifica si el paquete escaneado (código PD-001) pertenece a la ruta activa."""
    ruta = _obtener_ruta_activa_o_404(db, conductor_id)

    pedido = ruta_repository.obtener_pedido_por_codigo(db, codigo)
    if not pedido:
        return ValidacionQRResponse(
            pertenece=False,
            mensaje=f"El paquete '{codigo}' no existe en el sistema",
        )

    detalle = ruta_repository.obtener_detalle_de_ruta(db, ruta.id, pedido.id)
    if not detalle:
        return ValidacionQRResponse(
            pertenece=False,
            mensaje="Este paquete NO pertenece a tu ruta de hoy",
        )

    return ValidacionQRResponse(
        pertenece=True,
        mensaje="Paquete validado correctamente. Pertenece a tu ruta.",
        parada=_construir_parada(detalle, pedido),
    )


# FASE 3.3: Ejecución y evidencias (CUS-26 / CUS-29)
def _obtener_detalle_de_mi_ruta(
    db: Session, conductor_id: int, pedido_id: int
) -> RutaDetalle:
    """Recupera el detalle del pedido garantizando que pertenece a la ruta activa del conductor."""
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
    """CUS-26: marca un pedido como ENTREGADO o FALLIDO."""
    if estado == "FALLIDO" and not (motivo_fallo and motivo_fallo.strip()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debes indicar el motivo del fallo en una entrega fallida",
        )

    detalle = _obtener_detalle_de_mi_ruta(db, conductor_id, pedido_id)

    # CUS-30: bloquear si la ruta está pausada por una incidencia de auxilio mecánico.
    if incidencia_repository.tiene_abierta(db, detalle.ruta_id):
        raise HTTPException(status_code=400, detail="La ruta está pausada por una incidencia. Reanúdala antes de continuar.")

    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()

    ahora = datetime.utcnow()
    estado_anterior = pedido.estado
    detalle.estado_entrega = estado
    detalle.fecha_gestion = ahora
    detalle.motivo_fallo = motivo_fallo if estado == "FALLIDO" else None

    # Reflejamos el estado en el Pedido (trazabilidad para CUS-35)
    pedido.estado = estado
    pedido.fecha_entrega = ahora if estado == "ENTREGADO" else None

    # La primera gestión arranca la ruta (CREADA -> EN_PROGRESO)
    if detalle.ruta and detalle.ruta.estado == "CREADA":
        detalle.ruta.estado = "EN_PROGRESO"

    # Registramos el evento en el historial (quién = el conductor).
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
    """CUS-29: guarda la foto POD y la asocia al detalle de la ruta."""
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

    # URL pública servida por StaticFiles (montado en /media)
    url = f"/media/evidencias/{nombre_final}"
    detalle.url_evidencia = url
    db.commit()
    db.refresh(detalle)

    # Además del detalle, registramos la evidencia como POD propio (tabla del diagrama),
    # así la prueba de entrega queda persistida en la BD y es consultable por pedido.
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


# FASE 3.4: Cierre de operación (CUS-28)
def finalizar_ruta(db: Session, conductor_id: int) -> CierreRutaResponse:
    """CUS-28: da por finalizada la ruta del día del conductor."""
    ruta = _obtener_ruta_activa_o_404(db, conductor_id)

    # CUS-30: no se puede cerrar el día con una incidencia (auxilio mecánico) abierta.
    if incidencia_repository.tiene_abierta(db, ruta.id):
        raise HTTPException(status_code=400, detail="La ruta está pausada por una incidencia. Reanúdala antes de cerrar el día.")

    detalles = ruta_repository.obtener_detalles_con_pedido(db, ruta.id)

    pendientes = sum(1 for d, _ in detalles if d.estado_entrega == "PENDIENTE")
    entregadas = sum(1 for d, _ in detalles if d.estado_entrega == "ENTREGADO")
    fallidas = sum(1 for d, _ in detalles if d.estado_entrega == "FALLIDO")

    # No se puede cerrar el día con paradas sin gestionar: cada parada debe estar
    # entregada (con su evidencia) o reportada como fallida.
    if pendientes:
        raise HTTPException(
            status_code=400,
            detail=f"No puedes cerrar la ruta: quedan {pendientes} parada(s) pendiente(s) por gestionar.",
        )

    ruta.estado = "FINALIZADA"
    ruta.fecha_fin = datetime.utcnow()

    # CUS-28: horas trabajadas = cierre - salida. Si no hubo sello de salida (ruta
    # antigua), se usa la fecha de creación como referencia para no devolver vacío.
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


# FASE 2: Enrutamiento básico (CUS-18)
def asignar_bloque(db: Session, datos: AsignacionBloqueRequest, usuario_id: int | None = None) -> dict:
    """
    CUS-18: el admin crea una ruta para un conductor con TODOS los pedidos
    PENDIENTES de un distrito.
    Pasos: buscar pedidos -> crear la ruta -> colgar cada pedido como detalle
           (secuencia=0, aún sin optimizar) -> marcar pedidos como 'ASIGNADO'
           -> registrar el evento en el historial.
    """
    pedidos = pedido_repository.obtener_pendientes_por_distrito(db, datos.distrito)
    if not pedidos:
        raise HTTPException(status_code=400, detail="No hay pedidos pendientes para esa zona")

    # Un conductor no puede tener dos rutas activas a la vez (evita duplicados):
    # debe cerrar la actual antes de que se le asigne otra.
    if datos.conductor_id:
        activa = ruta_repository.obtener_ruta_activa_por_conductor(db, datos.conductor_id)
        if activa:
            raise HTTPException(
                status_code=400,
                detail=f"El conductor ya tiene una ruta activa ('{activa.nombre}'). Debe cerrarla antes de asignar otra.",
            )

    # El nombre se deriva de la zona ("Ruta Miraflores"). Si llega un nombre
    # explícito no vacío se respeta (override opcional); si no, se genera.
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


# FASE 2: Optimización VRP (CUS-19)
def optimizar_ruta(db: Session, datos: OptimizacionRequest, conductor_id: int) -> dict:
    """
    CUS-19: el conductor optimiza el orden de entrega de SU ruta partiendo de
    su posición actual. Usa el algoritmo del Vecino Más Cercano (router.py).
    """
    ruta = ruta_repository.obtener_ruta_por_id(db, datos.ruta_id)
    if not ruta:
        raise HTTPException(status_code=404, detail="Ruta no encontrada")

    # Seguridad: un conductor solo puede optimizar su propia ruta.
    if ruta.conductor_id != conductor_id:
        raise HTTPException(status_code=403, detail="Esta ruta no está asignada a tu usuario")

    # Tomamos los pedidos de la ruta que tienen coordenadas válidas.
    detalles = ruta_repository.obtener_detalles_con_pedido(db, ruta.id)
    pedidos_validos = [pedido for _, pedido in detalles if pedido.latitud is not None]
    if not pedidos_validos:
        raise HTTPException(status_code=400, detail="La ruta no tiene pedidos válidos para optimizar")

    # CEREBRO MATEMÁTICO: ordena los pedidos minimizando distancia (VRP greedy).
    ordenados = optimizar_secuencia_pedidos(
        pedidos_validos,
        datos.latitud_actual_conductor,
        datos.longitud_actual_conductor,
    )

    # Escribimos la secuencia final (1, 2, 3...) en cada detalle.
    secuencia = 1
    for pedido in ordenados:
        detalle = ruta_repository.obtener_detalle_de_ruta(db, ruta.id, pedido.id)
        detalle.secuencia = secuencia
        estado_anterior = pedido.estado
        pedido.estado = "EN_RUTA"
        historial_repository.registrar(db, pedido.id, estado_anterior, "EN_RUTA", conductor_id)
        secuencia += 1

    # CUS-23: iniciar la ruta = salir del almacén. La primera vez sellamos la salida y
    # pasamos la ruta a EN_PROGRESO; ese sello arranca el conteo de horas (CUS-28).
    if ruta.fecha_salida is None:
        ruta.fecha_salida = datetime.utcnow()
        ruta.estado = "EN_PROGRESO"

    ruta_repository.guardar_cambios(db)

    return {"mensaje": "Ruta optimizada matemáticamente", "total_paradas": len(ordenados)}


# FASE 5: ajuste manual de la ruta desde el panel (CUS-20)
def _ruta_o_404(db: Session, ruta_id: int) -> Ruta:
    """Devuelve la ruta o lanza 404."""
    ruta = ruta_repository.obtener_ruta_por_id(db, ruta_id)
    if not ruta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ruta no encontrada")
    return ruta


def obtener_paradas_admin(db: Session, ruta_id: int):
    """CUS-20: paradas de una ruta (ordenadas) para que el admin las edite en el panel."""
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
    """CUS-20: reescribe la secuencia de las paradas según el orden recibido (lista de
    pedido_id). Solo afecta a los pedidos que pertenecen a la ruta. Recibe: id de ruta
    y la lista ordenada de pedido_id."""
    ruta = _ruta_o_404(db, ruta_id)
    secuencia = 1
    vistos = set()
    for pedido_id in orden:
        detalle = ruta_repository.obtener_detalle_de_ruta(db, ruta.id, pedido_id)
        if detalle:
            detalle.secuencia = secuencia
            secuencia += 1
            vistos.add(pedido_id)
    # Defensa: si el orden recibido no incluía todas las paradas, las que faltan se
    # numeran al final para que NO queden secuencias duplicadas o solapadas.
    for detalle, pedido in ruta_repository.obtener_detalles_con_pedido(db, ruta.id):
        if pedido.id not in vistos:
            detalle.secuencia = secuencia
            secuencia += 1
    db.commit()
    return {"mensaje": "Orden de paradas actualizado", "total_paradas": secuencia - 1}


def quitar_parada(db: Session, ruta_id: int, pedido_id: int, usuario_id: int | None = None) -> dict:
    """CUS-20: quita un pedido de la ruta y lo devuelve a PENDIENTE para reasignarlo.
    Recibe: id de ruta, id de pedido y el id del admin."""
    ruta = _ruta_o_404(db, ruta_id)
    detalle = ruta_repository.obtener_detalle_de_ruta(db, ruta.id, pedido_id)
    if not detalle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Esa parada no pertenece a la ruta")

    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    db.delete(detalle)
    if pedido:
        estado_anterior = pedido.estado
        pedido.estado = "PENDIENTE"
        pedido.fecha_entrega = None
        historial_repository.registrar(db, pedido.id, estado_anterior, "PENDIENTE", usuario_id)
    db.commit()
    return {"mensaje": "Parada quitada de la ruta; el pedido volvió a PENDIENTE"}


# FASE 5: manifiesto descargable en Excel (CUS-21)
COLUMNAS_MANIFIESTO = ["Secuencia", "Código", "Cliente", "Destinatario", "Dirección", "Distrito", "Teléfono", "Estado"]


def generar_manifiesto_excel(db: Session, ruta_id: int) -> tuple[bytes, str]:
    """CUS-21: arma el manifiesto de carga de una ruta como archivo Excel (.xlsx) en
    memoria. Recibe: id de la ruta. Devuelve: (bytes del archivo, nombre sugerido)."""
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
