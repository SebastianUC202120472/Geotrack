# app/services/recojo_service.py
# Lógica del módulo Inbound de recojos: alta de solicitudes (CUS-10), asignación de
# ruta de recojo (CUS-11) y recepción condicionada en origen (CUS-12).
import os
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.solicitud_recojo import SolicitudRecojo
from app.models.pedido import Pedido
from app.models.cliente import ClienteCorporativo
from app.models.ruta import Ruta
from app.repositories import recojo_repository, ruta_repository, incidencia_repository
from app.services.geocoder import obtener_coordenadas
from app.services import notificaciones_service
from app.services.router import optimizar_secuencia_pedidos, distancia_total
from app.schemas.recojo import (
    SolicitudRecojoCreate,
    SolicitudRecojoUpdate,
    AsignarRutaRecojoRequest,
    AsignarRutaRecojoResponse,
    ManifiestoRecojoResponse,
    ParadaRecojo,
    RecepcionResponse,
    AceptarSolicitudResponse,
    SolicitudArmarItem,
)
from app.services import pedido_service as _pedido_svc
from app.schemas.ruta import OptimizacionRequest, CierreRutaResponse

# Carpeta donde se guardan las fotos de las Guías de Remisión (servidas en /media/guias).
DIR_GUIAS = os.path.join("uploads", "guias")
EXTENSIONES_IMAGEN = {".jpg", ".jpeg", ".png", ".webp"}


def _distrito_de(direccion: str) -> str:
    """Deriva el distrito del texto de la dirección (igual que pedidos, CUS-16):
    toma lo que va tras la primera coma. Recibe: la dirección de origen."""
    partes = (direccion or "").split(",")
    return partes[1].strip() if len(partes) >= 2 else "ZONA_DESCONOCIDA"


# === CUS-10: alta de solicitud de recojo (admin) ===
def crear_solicitud(db: Session, datos: SolicitudRecojoCreate, usuario_id: int | None = None) -> SolicitudRecojo:
    """Crea una solicitud de recojo: valida el cliente, geocodifica el origen y la deja
    en SOLICITADO. Recibe: los datos del formulario (CUS-10)."""
    cliente = db.query(ClienteCorporativo).filter(ClienteCorporativo.id == datos.cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=400, detail="El cliente indicado no existe")

    direccion = (datos.direccion_origen or "").strip()
    if not direccion:
        raise HTTPException(status_code=400, detail="La dirección de origen es obligatoria")
    if datos.volumen_estimado_m3 is not None and datos.volumen_estimado_m3 < 0:
        raise HTTPException(status_code=400, detail="El volumen estimado no puede ser negativo")

    lat, lng = obtener_coordenadas(direccion)
    recojo = SolicitudRecojo(
        cliente_id=cliente.id,
        cliente_origen=cliente.razon_social,
        direccion_origen=direccion,
        distrito=_distrito_de(direccion) if (lat and lng) else None,
        latitud=lat,
        longitud=lng,
        volumen_estimado_m3=datos.volumen_estimado_m3,
        contacto_origen=datos.contacto_origen,
        referencia=datos.referencia,
        conversacion_id=datos.conversacion_id,
        estado="SOLICITADO",
    )
    recojo_repository.agregar(db, recojo)
    recojo_repository.guardar_cambios(db)
    db.refresh(recojo)
    # Notifica al admin que llegó una solicitud de recojo nueva.
    try:
        notificaciones_service.registrar(
            db, "recojos", "Nueva solicitud de recojo",
            f"{cliente.razon_social} — {direccion}", "/bandeja", recojo.id)
    except Exception:
        pass
    return recojo


def listar_solicitudes(db: Session, estado: str | None = None):
    """Lista las solicitudes de recojo (filtro opcional por estado)."""
    return recojo_repository.listar(db, estado)


def obtener_solicitud(db: Session, recojo_id: int) -> SolicitudRecojo:
    """Devuelve una solicitud por id, o 404 si no existe. Recibe: id del recojo."""
    recojo = recojo_repository.obtener_por_id(db, recojo_id)
    if not recojo:
        raise HTTPException(status_code=404, detail="Solicitud de recojo no encontrada")
    return recojo


def editar_solicitud(db: Session, recojo_id: int, datos: SolicitudRecojoUpdate) -> SolicitudRecojo:
    """Edita una solicitud mientras está SOLICITADO; re-geocodifica si cambió la dirección.
    Recibe: id del recojo y los campos a actualizar."""
    recojo = obtener_solicitud(db, recojo_id)
    if recojo.estado != "SOLICITADO":
        raise HTTPException(status_code=400, detail="Solo se puede editar una solicitud en estado SOLICITADO")

    if datos.direccion_origen is not None:
        direccion = datos.direccion_origen.strip()
        if not direccion:
            raise HTTPException(status_code=400, detail="La dirección de origen es obligatoria")
        recojo.direccion_origen = direccion
        lat, lng = obtener_coordenadas(direccion)
        recojo.latitud = lat
        recojo.longitud = lng
        recojo.distrito = _distrito_de(direccion) if (lat and lng) else None
    if datos.volumen_estimado_m3 is not None:
        if datos.volumen_estimado_m3 < 0:
            raise HTTPException(status_code=400, detail="El volumen estimado no puede ser negativo")
        recojo.volumen_estimado_m3 = datos.volumen_estimado_m3
    if datos.contacto_origen is not None:
        recojo.contacto_origen = datos.contacto_origen
    if datos.referencia is not None:
        recojo.referencia = datos.referencia

    recojo_repository.guardar_cambios(db)
    db.refresh(recojo)
    return recojo


# === Aceptar solicitud con Excel: crea el recojo y los pedidos POR_RECOGER ===
def aceptar_solicitud(
    db: Session,
    cliente_id: int,
    contenido: bytes,
    nombre_archivo: str,
    referencia: str | None,
    contacto_origen: str | None,
    usuario_id: int | None,
) -> AceptarSolicitudResponse:
    """Acepta una solicitud de recojo cargada por el admin con un Excel de pedidos.
    Recibe: id de cliente, bytes del archivo, nombre del archivo, referencia, contacto
    y el id del admin. Crea el recojo en SOLICITADO (origen del cliente) y un pedido
    POR_RECOGER por cada fila válida del Excel."""
    # Validar que el cliente exista y no esté eliminado.
    cliente = (
        db.query(ClienteCorporativo)
        .filter(ClienteCorporativo.id == cliente_id, ClienteCorporativo.eliminado_en.is_(None))
        .first()
    )
    if not cliente:
        raise HTTPException(status_code=400, detail="El cliente indicado no existe o fue eliminado")
    if cliente.latitud is None or cliente.longitud is None:
        raise HTTPException(status_code=400, detail="El cliente no tiene una ubicación de recojo registrada")

    # Parsear el Excel ANTES de crear el recojo: si el archivo es inválido, no debe quedar
    # un recojo huérfano (sin pedidos) en la base de datos.
    filas = _pedido_svc.parsear_filas_excel(contenido, nombre_archivo)

    # Crear el recojo copiando la ubicación del cliente (sin re-geocodificar).
    recojo = SolicitudRecojo(
        cliente_id=cliente.id,
        cliente_origen=cliente.razon_social,
        direccion_origen=cliente.direccion_origen,
        distrito=cliente.distrito,
        latitud=cliente.latitud,
        longitud=cliente.longitud,
        estado="SOLICITADO",
        referencia=referencia,
        contacto_origen=contacto_origen,
    )
    recojo_repository.agregar(db, recojo)
    recojo_repository.guardar_cambios(db)
    db.refresh(recojo)

    # Crear un pedido por cada fila válida del Excel ya parseado.
    filas_rechazadas: list[str] = []
    pedidos_creados = 0
    pedidos_geocodificados = 0

    for i, fila in enumerate(filas, start=1):
        # Validar campos mínimos por fila.
        if not (fila.get("referencia_externa") or "").strip():
            filas_rechazadas.append(f"Fila {i}: falta referencia_externa")
            continue
        if not (fila.get("direccion_destino") or "").strip():
            filas_rechazadas.append(f"Fila {i}: falta direccion_destino")
            continue

        pedido = _pedido_svc.crear_pedido_desde_fila(
            db, fila, cliente, recojo.id, "POR_RECOGER", usuario_id
        )
        pedidos_creados += 1
        if pedido.latitud is not None:
            pedidos_geocodificados += 1

    return AceptarSolicitudResponse(
        recojo_id=recojo.id,
        codigo=recojo.codigo,
        pedidos_creados=pedidos_creados,
        pedidos_geocodificados=pedidos_geocodificados,
        pedidos_sin_ubicar=pedidos_creados - pedidos_geocodificados,
        filas_rechazadas=filas_rechazadas,
    )


# === Armado de ruta de recojo (almacén) ===
def listar_para_armar(db: Session) -> list[SolicitudArmarItem]:
    """Devuelve las solicitudes en estado SOLICITADO con el número de pedidos asociados,
    listas para que el almacén arme la ruta. Recibe: sesión de base de datos."""
    recojos = recojo_repository.listar(db, estado="SOLICITADO")
    resultado = []
    for r in recojos:
        num_pedidos = db.query(Pedido).filter(Pedido.recojo_id == r.id).count()
        resultado.append(SolicitudArmarItem(
            id=r.id,
            codigo=r.codigo,
            cliente_origen=r.cliente_origen,
            direccion_origen=r.direccion_origen,
            distrito=r.distrito,
            num_pedidos=num_pedidos,
        ))
    return resultado


# === CUS-11: asignar una ruta de recojo (admin) ===
def asignar_ruta_recojo(db: Session, datos: AsignarRutaRecojoRequest, usuario_id: int | None = None) -> AsignarRutaRecojoResponse:
    """Crea una ruta de recojo (tipo=RECOJO) con conductor + vehículo y le cuelga las
    solicitudes seleccionadas. Valida que estén SOLICITADO y que el conductor esté libre.
    Recibe: recojo_ids, conductor_id, vehiculo_placa y nombre opcional (CUS-11)."""
    if not datos.recojo_ids:
        raise HTTPException(status_code=400, detail="Selecciona al menos una solicitud de recojo")

    recojos = recojo_repository.obtener_por_ids(db, datos.recojo_ids)
    if len(recojos) != len(set(datos.recojo_ids)):
        raise HTTPException(status_code=400, detail="Alguna solicitud seleccionada no existe")
    no_disponibles = [r.codigo or r.id for r in recojos if r.estado != "SOLICITADO"]
    if no_disponibles:
        raise HTTPException(status_code=400, detail=f"Estas solicitudes ya no están disponibles: {no_disponibles}")

    activa = ruta_repository.obtener_ruta_activa_por_conductor(db, datos.conductor_id)
    if activa:
        raise HTTPException(
            status_code=400,
            detail=f"El conductor ya tiene una ruta activa ('{activa.nombre}'). Debe cerrarla antes de asignar otra.",
        )

    # Nombre por defecto: "Recojo <distrito del primer recojo con distrito>".
    distrito = next((r.distrito for r in recojos if r.distrito), None)
    nombre = (datos.nombre_ruta or "").strip() or f"Recojo {distrito or 'sin zona'}"

    ruta = ruta_repository.crear_ruta(db, nombre=nombre, conductor_id=datos.conductor_id)
    ruta.tipo = "RECOJO"
    ruta.vehiculo_placa = datos.vehiculo_placa

    for recojo in recojos:
        recojo.ruta_id = ruta.id
        recojo.secuencia = 0
        recojo.estado = "ASIGNADO"

    ruta_repository.guardar_cambios(db)
    return AsignarRutaRecojoResponse(
        mensaje=f"{len(recojos)} recojo(s) asignados a la ruta '{nombre}'",
        ruta_id=ruta.id,
        codigo=ruta.codigo,
    )


# === CUS-12: lado conductor ===
def _ruta_recojo_activa_o_404(db: Session, conductor_id: int) -> Ruta:
    """Devuelve la ruta de recojo activa del conductor (404 si no tiene ruta, 400 si su
    ruta activa no es de recojo). Recibe: id del conductor."""
    ruta = ruta_repository.obtener_ruta_activa_por_conductor(db, conductor_id)
    if not ruta:
        raise HTTPException(status_code=404, detail="No tienes una ruta activa asignada")
    if ruta.tipo != "RECOJO":
        raise HTTPException(status_code=400, detail="Tu ruta activa no es de recojo")
    return ruta


def obtener_manifiesto_recojo(db: Session, conductor_id: int) -> ManifiestoRecojoResponse:
    """CUS-12: manifiesto de la ruta de recojo activa, con los puntos de origen ordenados
    por secuencia. Recibe: id del conductor."""
    ruta = _ruta_recojo_activa_o_404(db, conductor_id)
    recojos = recojo_repository.obtener_por_ruta(db, ruta.id)
    paradas = [
        ParadaRecojo(
            secuencia=r.secuencia or 0,
            recojo_id=r.id,
            codigo=r.codigo,
            cliente_origen=r.cliente_origen,
            direccion_origen=r.direccion_origen,
            distrito=r.distrito,
            latitud=r.latitud,
            longitud=r.longitud,
            volumen_estimado_m3=r.volumen_estimado_m3,
            estado=r.estado,
            cantidad_declarada=r.cantidad_declarada,
            url_guia=r.url_guia,
        )
        for r in recojos
    ]
    return ManifiestoRecojoResponse(
        ruta_id=ruta.id, codigo=ruta.codigo, nombre=ruta.nombre, estado=ruta.estado,
        total_paradas=len(paradas), paradas=paradas,
    )


def optimizar_recojo(db: Session, datos: OptimizacionRequest, conductor_id: int) -> dict:
    """CUS-19 (recojo): optimiza la secuencia de la ruta de recojo desde la posición del
    conductor (reusa el VRP de pedidos). Sella la salida y pasa ruta + recojos a EN_RUTA.
    Recibe: ruta_id + lat/lng actuales del conductor."""
    ruta = ruta_repository.obtener_ruta_por_id(db, datos.ruta_id)
    if not ruta:
        raise HTTPException(status_code=404, detail="Ruta no encontrada")
    if ruta.conductor_id != conductor_id:
        raise HTTPException(status_code=403, detail="Esta ruta no está asignada a tu usuario")
    if ruta.tipo != "RECOJO":
        raise HTTPException(status_code=400, detail="Esta ruta no es de recojo")

    recojos = recojo_repository.obtener_por_ruta(db, ruta.id)
    validos = [r for r in recojos if r.latitud is not None]
    if not validos:
        raise HTTPException(status_code=400, detail="La ruta no tiene puntos válidos para optimizar")

    ordenados = optimizar_secuencia_pedidos(
        validos, datos.latitud_actual_conductor, datos.longitud_actual_conductor
    )

    origen = (datos.latitud_actual_conductor, datos.longitud_actual_conductor)
    km_base = distancia_total(origen[0], origen[1], validos)
    km_opt = distancia_total(origen[0], origen[1], ordenados)
    ruta.km_estimado = round(km_opt, 2)
    ruta.km_ahorrado = round(max(0.0, km_base - km_opt), 2)

    secuencia = 1
    for recojo in ordenados:
        recojo.secuencia = secuencia
        if recojo.estado == "ASIGNADO":
            recojo.estado = "EN_RUTA"
        secuencia += 1

    # CUS-23: la primera optimización = salida del almacén.
    if ruta.fecha_salida is None:
        ruta.fecha_salida = datetime.utcnow()
        ruta.estado = "EN_PROGRESO"

    ruta_repository.guardar_cambios(db)
    return {"mensaje": "Ruta de recojo optimizada", "total_paradas": len(ordenados)}


def registrar_recepcion(db: Session, conductor_id: int, recojo_id: int, cantidad_declarada: int,
                        contenido: bytes, nombre_archivo: str) -> RecepcionResponse:
    """CUS-12: recepción condicionada a bulto cerrado. Valida pertenencia y pausa, guarda la
    foto de la Guía de Remisión y deja el recojo en RECOGIDO. Recibe: conductor, recojo_id,
    cantidad declarada (>0), bytes y nombre de la foto."""
    if cantidad_declarada is None or cantidad_declarada <= 0:
        raise HTTPException(status_code=400, detail="La cantidad declarada debe ser un entero mayor que 0")

    ruta = _ruta_recojo_activa_o_404(db, conductor_id)

    # CUS-30: si la ruta está pausada por una incidencia, no se puede registrar.
    if incidencia_repository.tiene_abierta(db, ruta.id):
        raise HTTPException(status_code=400, detail="La ruta está pausada por una incidencia. Reanúdala antes de continuar.")

    recojo = recojo_repository.obtener_por_id(db, recojo_id)
    if not recojo or recojo.ruta_id != ruta.id:
        raise HTTPException(status_code=404, detail="Este recojo no pertenece a tu ruta activa")
    if recojo.estado == "RECOGIDO":
        raise HTTPException(status_code=400, detail="Este recojo ya fue registrado")

    _, extension = os.path.splitext(nombre_archivo.lower())
    if extension not in EXTENSIONES_IMAGEN:
        raise HTTPException(status_code=400, detail=f"Formato no permitido. Usa: {', '.join(sorted(EXTENSIONES_IMAGEN))}")

    os.makedirs(DIR_GUIAS, exist_ok=True)
    nombre_final = f"guia_{ruta.id}_{recojo_id}{extension}"
    ruta_fisica = os.path.join(DIR_GUIAS, nombre_final)
    with open(ruta_fisica, "wb") as f:
        f.write(contenido)

    recojo.url_guia = f"/media/guias/{nombre_final}"
    recojo.cantidad_declarada = cantidad_declarada
    recojo.estado = "RECOGIDO"
    recojo.fecha_recojo = datetime.utcnow()

    if ruta.estado == "CREADA":
        ruta.estado = "EN_PROGRESO"

    recojo_repository.guardar_cambios(db)
    db.refresh(recojo)
    return RecepcionResponse(
        recojo_id=recojo.id, codigo=recojo.codigo, estado=recojo.estado,
        cantidad_declarada=recojo.cantidad_declarada, url_guia=recojo.url_guia,
        fecha_recojo=recojo.fecha_recojo, mensaje="Recepción registrada correctamente",
    )


def finalizar_ruta_recojo(db: Session, ruta: Ruta) -> CierreRutaResponse:
    """CUS-28 (recojo): cierra una ruta de recojo. Exige que no queden recojos pendientes.
    Recibe: la ruta de recojo activa (la pasa ruta_service.finalizar_ruta)."""
    if incidencia_repository.tiene_abierta(db, ruta.id):
        raise HTTPException(status_code=400, detail="La ruta está pausada por una incidencia. Reanúdala antes de cerrar el día.")

    recojos = recojo_repository.obtener_por_ruta(db, ruta.id)
    pendientes = sum(1 for r in recojos if r.estado != "RECOGIDO")
    recogidas = sum(1 for r in recojos if r.estado == "RECOGIDO")
    if pendientes:
        raise HTTPException(status_code=400, detail=f"No puedes cerrar la ruta: quedan {pendientes} recojo(s) pendiente(s).")

    ruta.estado = "FINALIZADA"
    ruta.fecha_fin = datetime.utcnow()
    if ruta.km_estimado is None and recojos:
        primero = next((r for r in recojos if r.latitud is not None), None)
        if primero is not None:
            ruta.km_estimado = round(distancia_total(primero.latitud, primero.longitud, recojos), 2)
            ruta.km_ahorrado = 0.0

    hora_inicio = ruta.fecha_salida or ruta.fecha_creacion
    duracion = None
    if hora_inicio:
        duracion = max(0, int((ruta.fecha_fin - hora_inicio).total_seconds() // 60))

    db.commit()
    return CierreRutaResponse(
        ruta_id=ruta.id, codigo=ruta.codigo, nombre=ruta.nombre, estado=ruta.estado,
        fecha_fin=ruta.fecha_fin, hora_inicio=hora_inicio, hora_fin=ruta.fecha_fin,
        duracion_minutos=duracion, total_paradas=len(recojos), entregadas=recogidas,
        fallidas=0, pendientes=pendientes, mensaje="Ruta de recojo finalizada correctamente",
    )
