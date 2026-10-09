import os
import secrets
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.imagenes import validar_imagen
from app.models.solicitud_recojo import SolicitudRecojo, ESTADOS_RECOGIDO, ESTADOS_GESTIONADOS
from app.models.pedido import Pedido
from app.models.cliente import ClienteCorporativo
from app.models.ruta import Ruta
from app.repositories import recojo_repository, ruta_repository, incidencia_repository, pedido_repository
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
    SolicitudManualCreate,
    RutaRecojoItem,
)
from app.core.fechas import hoy_local
from app.services import pedido_service as _pedido_svc
from app.schemas.ruta import OptimizacionRequest, CierreRutaResponse

DIR_GUIAS = os.path.join("uploads", "guias")


def _distrito_de(direccion: str) -> str:
    """Extrae el distrito de una dirección tomando el texto tras la primera coma. Recibe: direccion."""
    partes = (direccion or "").split(",")
    return partes[1].strip() if len(partes) >= 2 else "ZONA_DESCONOCIDA"


def crear_solicitud(db: Session, datos: SolicitudRecojoCreate, usuario_id: int | None = None) -> SolicitudRecojo:
    """Crea una solicitud de recojo geocodificando el origen. Recibe: datos del formulario."""
    cliente = db.query(ClienteCorporativo).filter(ClienteCorporativo.id == datos.cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=400, detail="El cliente indicado no existe")

    direccion = (datos.direccion_origen or "").strip()
    if not direccion:
        raise HTTPException(status_code=400, detail="La dirección de origen es obligatoria")
    if datos.volumen_estimado_m3 is not None and datos.volumen_estimado_m3 < 0:
        raise HTTPException(status_code=400, detail="El volumen estimado no puede ser negativo")
    _validar_fecha_programada(datos.fecha_programada)

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
        fecha_programada=datos.fecha_programada,
        estado="SOLICITADO",
    )
    recojo_repository.agregar(db, recojo)
    recojo_repository.guardar_cambios(db)
    db.refresh(recojo)
    try:
        notificaciones_service.registrar(
            db, "recojos", "Nueva solicitud de recojo",
            f"{cliente.razon_social} — {direccion}", "/bandeja", recojo.id)
    except Exception:
        pass
    return recojo


def _validar_fecha_programada(fecha) -> None:
    """Rechaza una fecha de recojo pasada (C11-04). Recibe la fecha (o None = sin fecha)."""
    if fecha is not None and fecha < hoy_local():
        raise HTTPException(status_code=400, detail="La fecha de recojo no puede ser anterior a hoy")


def listar_solicitudes(db: Session, estado: str | None = None):
    """Lista solicitudes de recojo (filtro opcional por estado) con su numero de pedidos. Recibe: estado."""
    recojos = recojo_repository.listar(db, estado)
    totales = pedido_repository.totales_por_recojo(db, [r.id for r in recojos])
    for r in recojos:
        r.num_pedidos = totales.get(r.id, (0, 0.0, 0.0))[0]
    return recojos


def obtener_solicitud(db: Session, recojo_id: int) -> SolicitudRecojo:
    """Devuelve una solicitud por id o lanza 404. Recibe: recojo_id."""
    recojo = recojo_repository.obtener_por_id(db, recojo_id)
    if not recojo:
        raise HTTPException(status_code=404, detail="Solicitud de recojo no encontrada")
    return recojo


def editar_solicitud(db: Session, recojo_id: int, datos: SolicitudRecojoUpdate) -> SolicitudRecojo:
    """Edita una solicitud en estado SOLICITADO y re-geocodifica si cambia la dirección. Recibe: recojo_id, datos."""
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
    if "fecha_programada" in datos.model_fields_set:
        _validar_fecha_programada(datos.fecha_programada)
        recojo.fecha_programada = datos.fecha_programada

    recojo_repository.guardar_cambios(db)
    db.refresh(recojo)
    recojo.num_pedidos = pedido_repository.totales_por_recojo(db, [recojo.id]).get(recojo.id, (0, 0, 0))[0]
    return recojo


def _cliente_para_recojo(db: Session, cliente_id: int) -> ClienteCorporativo:
    """Devuelve el cliente activo y con punto de recojo ubicado, o lanza 400. Recibe el cliente_id."""
    cliente = (
        db.query(ClienteCorporativo)
        .filter(ClienteCorporativo.id == cliente_id, ClienteCorporativo.eliminado_en.is_(None))
        .first()
    )
    if not cliente:
        raise HTTPException(status_code=400, detail="El cliente indicado no existe o fue eliminado")
    if cliente.latitud is None or cliente.longitud is None:
        raise HTTPException(
            status_code=400,
            detail="El cliente no tiene ubicada su dirección de recojo. Ubícala en Clientes antes de registrar la solicitud.",
        )
    return cliente


def _filtrar_filas(db: Session, cliente, filas: list[dict], etiqueta: str = "Fila") -> tuple[list[dict], list[str], int]:
    """Separa las filas validas de las rechazadas: sin referencia o direccion, repetidas en el archivo
    o que ya existen como pedido vigente del cliente (C11-01). Recibe el cliente, las filas y como
    nombrar cada fila. Devuelve (validas, motivos de rechazo, cuantas eran duplicadas)."""
    existentes = pedido_repository.referencias_existentes(
        db, cliente.id, [f.get("referencia_externa") for f in filas])
    vistas: set[str] = set()
    validas: list[dict] = []
    rechazadas: list[str] = []
    duplicadas = 0
    for i, fila in enumerate(filas, start=1):
        ref = (fila.get("referencia_externa") or "").strip()
        if not ref:
            rechazadas.append(f"{etiqueta} {i}: falta referencia_externa")
        elif not (fila.get("direccion_destino") or "").strip():
            rechazadas.append(f"{etiqueta} {i}: falta direccion_destino")
        elif ref in vistas:
            rechazadas.append(f"{etiqueta} {i}: la referencia {ref} está repetida")
            duplicadas += 1
        elif ref in existentes:
            rechazadas.append(f"{etiqueta} {i}: el pedido {ref} ya está registrado ({existentes[ref]})")
            duplicadas += 1
        else:
            vistas.add(ref)
            fila["referencia_externa"] = ref
            validas.append(fila)
    return validas, rechazadas, duplicadas


def _exigir_filas_validas(validas: list, rechazadas: list[str], duplicadas: int) -> None:
    """Corta el registro si ninguna fila se puede importar; 409 si todas ya existian (reintento). Recibe el resultado del filtro."""
    if validas:
        return
    detalle = "; ".join(rechazadas[:5]) + (f" (y {len(rechazadas) - 5} más)" if len(rechazadas) > 5 else "")
    if rechazadas and duplicadas == len(rechazadas):
        raise HTTPException(
            status_code=409,
            detail=f"Todos los pedidos ya estaban registrados: no se creó nada para no duplicarlos. {detalle}",
        )
    raise HTTPException(status_code=400, detail=f"No hay pedidos válidos para registrar. {detalle}".strip())


def _crear_recojo_con_pedidos(db: Session, cliente, filas: list[dict], referencia, contacto_origen,
                              fecha_programada, usuario_id) -> SolicitudRecojo:
    """Crea la solicitud (en el punto de recojo del cliente) y sus pedidos POR_RECOGER sin hacer commit.
    Recibe el cliente, las filas ya validadas y los datos de la solicitud."""
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
        fecha_programada=fecha_programada,
    )
    recojo_repository.agregar(db, recojo)  # flush -> recojo.id disponible (sin commit)
    _pedido_svc.crear_pedidos_bulk(db, filas, cliente, recojo.id, "POR_RECOGER", usuario_id)
    return recojo


def aceptar_solicitud(
    db: Session,
    cliente_id: int,
    contenido: bytes,
    nombre_archivo: str,
    referencia: str | None,
    contacto_origen: str | None,
    usuario_id: int | None,
    conversacion_id: int | None = None,
    fecha_programada=None,
) -> AceptarSolicitudResponse:
    """Acepta una solicitud con Excel del admin: crea el recojo y un pedido POR_RECOGER por fila válida.
    Rechaza los pedidos que ya existen para el cliente, asi un reintento no duplica nada (C11-01).
    Recibe: cliente_id, bytes del Excel, metadatos y la fecha de recojo pedida."""
    cliente = _cliente_para_recojo(db, cliente_id)
    _validar_fecha_programada(fecha_programada)

    # Idempotencia: si la conversación ya fue ATENDIDA, evita duplicados ante reintentos.
    from app.repositories import correo_repository
    conv = correo_repository.obtener_conversacion(db, conversacion_id) if conversacion_id else None
    if conv and conv.estado == "ATENDIDA":
        raise HTTPException(
            status_code=409,
            detail="Esta solicitud ya fue aceptada (la conversación está ATENDIDA). No se crearon pedidos duplicados.",
        )

    # Parsear y filtrar antes de crear el recojo para no dejar recojos huérfanos.
    filas = _pedido_svc.parsear_filas_excel(contenido, nombre_archivo)
    validas, rechazadas, duplicadas = _filtrar_filas(db, cliente, filas)
    _exigir_filas_validas(validas, rechazadas, duplicadas)

    recojo = _crear_recojo_con_pedidos(db, cliente, validas, referencia, contacto_origen, fecha_programada, usuario_id)
    pedidos_creados = len(validas)

    if conv:
        recojo.conversacion_id = conversacion_id
        conv.estado = "ATENDIDA"

    db.commit()

    # Confirmación al cliente por correo (best-effort, fuera de la transacción).
    if conv:
        from app.services import correo_service
        try:
            correo_service.enviar_confirmacion_recojo(db, conv, pedidos_creados, usuario_id)
        except Exception:
            pass

    return AceptarSolicitudResponse(
        recojo_id=recojo.id,
        codigo=recojo.codigo,
        pedidos_creados=pedidos_creados,
        pedidos_geocodificados=0,            # se resuelven en segundo plano (ver endpoint)
        pedidos_sin_ubicar=pedidos_creados,  # todos pendientes de ubicar al responder
        geocodificacion_en_segundo_plano=True,
        filas_rechazadas=rechazadas,
    )


def registrar_solicitud_manual(db: Session, datos: SolicitudManualCreate, usuario_id: int | None) -> AceptarSolicitudResponse:
    """Registra una solicitud pedida por telefono con sus pedidos escritos a mano (C11-02).
    Aplica el mismo control de duplicados que el Excel. Recibe los datos del formulario y el usuario."""
    cliente = _cliente_para_recojo(db, datos.cliente_id)
    _validar_fecha_programada(datos.fecha_programada)
    filas = [
        {**p.model_dump(), "peso_kg": p.peso_kg or 0.0, "volumen_m3": p.volumen_m3 or 0.0}
        for p in datos.pedidos
    ]
    validas, rechazadas, duplicadas = _filtrar_filas(db, cliente, filas, etiqueta="Pedido")
    _exigir_filas_validas(validas, rechazadas, duplicadas)

    recojo = _crear_recojo_con_pedidos(
        db, cliente, validas, datos.referencia, datos.contacto_origen, datos.fecha_programada, usuario_id)
    db.commit()
    return AceptarSolicitudResponse(
        recojo_id=recojo.id,
        codigo=recojo.codigo,
        pedidos_creados=len(validas),
        pedidos_geocodificados=0,
        pedidos_sin_ubicar=len(validas),
        geocodificacion_en_segundo_plano=True,
        filas_rechazadas=rechazadas,
    )


def geocodificar_pedidos_recojo(recojo_id: int) -> None:
    """Geocodifica en segundo plano los pedidos sin ubicar de un recojo, en lotes de 20. Recibe: recojo_id."""
    from app.db.database import SessionLocal

    db = SessionLocal()
    try:
        pedidos = (
            db.query(Pedido)
            .filter(
                Pedido.recojo_id == recojo_id,
                Pedido.latitud.is_(None),
                Pedido.estado.in_(("POR_RECOGER", "LISTO_PARA_ENVIO")),
            )
            .all()
        )
        pendientes_commit = 0
        for pedido in pedidos:
            lat, lng = obtener_coordenadas(pedido.direccion_destino, db)  # con caché de direcciones
            if lat and lng:
                pedido.latitud = lat
                pedido.longitud = lng
                partes = pedido.direccion_destino.split(",")
                pedido.distrito = partes[1].strip() if len(partes) >= 2 else "ZONA_DESCONOCIDA"
                pendientes_commit += 1
                if pendientes_commit >= 20:
                    db.commit()
                    pendientes_commit = 0
        if pendientes_commit:
            db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


def listar_para_armar(db: Session) -> list[SolicitudArmarItem]:
    """Lista solicitudes SOLICITADO con ubicacion, volumen y fecha pedida para armar la ruta de recojo
    (C12-03), las de fecha mas cercana primero. Recibe: db."""
    recojos = recojo_repository.listar(db, estado="SOLICITADO")
    totales = pedido_repository.totales_por_recojo(db, [r.id for r in recojos])
    resultado = []
    for r in recojos:
        n, volumen, peso = totales.get(r.id, (0, 0.0, 0.0))
        resultado.append(SolicitudArmarItem(
            id=r.id,
            codigo=r.codigo,
            cliente_origen=r.cliente_origen,
            direccion_origen=r.direccion_origen,
            distrito=r.distrito,
            num_pedidos=n,
            latitud=r.latitud,
            longitud=r.longitud,
            volumen_m3=round(volumen or (r.volumen_estimado_m3 or 0.0), 3),
            peso_kg=round(peso, 2),
            fecha_programada=r.fecha_programada,
            referencia=r.referencia,
            contacto_origen=r.contacto_origen,
            motivo_no_realizado=r.motivo_no_realizado,
            intentos_no_realizados=r.intentos_no_realizados or 0,
        ))
    lejana = hoy_local() + timedelta(days=36500)
    resultado.sort(key=lambda x: (x.fecha_programada or lejana, x.id))
    return resultado


def asignar_ruta_recojo(db: Session, datos: AsignarRutaRecojoRequest, usuario_id: int | None = None) -> AsignarRutaRecojoResponse:
    """Crea una ruta de tipo RECOJO y asocia las solicitudes seleccionadas al conductor. Recibe: recojo_ids, conductor_id, vehiculo_placa."""
    if not datos.recojo_ids:
        raise HTTPException(status_code=400, detail="Selecciona al menos una solicitud de recojo")

    from app.services import conductor_service  # import local: evita ciclo de imports
    _, vehiculo = conductor_service.validar_para_ruta(db, datos.conductor_id)

    recojos = recojo_repository.obtener_por_ids(db, datos.recojo_ids, bloquear=True)
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

    # Nombre por defecto usa el distrito si es válido; sino la razón social del cliente.
    distrito = next((r.distrito for r in recojos if r.distrito and r.distrito != "ZONA_DESCONOCIDA"), None)
    cliente = next((r.cliente_origen for r in recojos if r.cliente_origen), None)
    nombre = (datos.nombre_ruta or "").strip() or f"Recojo {distrito or cliente or 'sin zona'}"

    ruta = ruta_repository.crear_ruta(db, nombre=nombre, conductor_id=datos.conductor_id)
    ruta.tipo = "RECOJO"
    ruta.vehiculo_placa = vehiculo.placa  # la del vehiculo vinculado al conductor (C12-01)

    for recojo in recojos:
        recojo.ruta_id = ruta.id
        recojo.secuencia = 0
        recojo.estado = "ASIGNADO"

    ruta_repository.guardar_cambios(db)
    return AsignarRutaRecojoResponse(
        mensaje=f"{len(recojos)} recojo(s) asignados a la ruta '{nombre}' con el vehículo {vehiculo.placa}",
        ruta_id=ruta.id,
        codigo=ruta.codigo,
    )


def _ruta_recojo_activa_o_404(db: Session, conductor_id: int) -> Ruta:
    """Devuelve la ruta de recojo activa del conductor o lanza 404/400. Recibe: conductor_id."""
    ruta = ruta_repository.obtener_ruta_activa_por_conductor(db, conductor_id)
    if not ruta:
        raise HTTPException(status_code=404, detail="No tienes una ruta activa asignada")
    if ruta.tipo != "RECOJO":
        raise HTTPException(status_code=400, detail="Tu ruta activa no es de recojo")
    return ruta


def obtener_manifiesto_recojo(db: Session, conductor_id: int) -> ManifiestoRecojoResponse:
    """Devuelve el manifiesto de la ruta de recojo activa ordenado por secuencia. Recibe: conductor_id."""
    ruta = _ruta_recojo_activa_o_404(db, conductor_id)
    recojos = recojo_repository.obtener_por_ruta(db, ruta.id)
    totales = pedido_repository.totales_por_recojo(db, [r.id for r in recojos])
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
            contacto_origen=r.contacto_origen,
            motivo_no_realizado=r.motivo_no_realizado if r.estado == "NO_REALIZADO" else None,
            num_pedidos=totales.get(r.id, (0, 0, 0))[0],
        )
        for r in recojos
    ]
    return ManifiestoRecojoResponse(
        ruta_id=ruta.id, codigo=ruta.codigo, nombre=ruta.nombre, estado=ruta.estado,
        total_paradas=len(paradas), paradas=paradas,
    )


def optimizar_recojo(db: Session, datos: OptimizacionRequest, conductor_id: int) -> dict:
    """Optimiza la secuencia de la ruta de recojo desde la posición del conductor y la pasa a EN_RUTA. Recibe: ruta_id, lat/lng del conductor."""
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

    if ruta.fecha_salida is None:
        ruta.fecha_salida = datetime.utcnow()
        ruta.estado = "EN_PROGRESO"

    ruta_repository.guardar_cambios(db)
    return {"mensaje": "Ruta de recojo optimizada", "total_paradas": len(ordenados)}


def registrar_recepcion(db: Session, conductor_id: int, recojo_id: int, cantidad_declarada: int,
                        archivos: list[tuple[bytes, str]], latitud: float | None = None,
                        longitud: float | None = None) -> RecepcionResponse:
    """Registra la recepción de un recojo con fotos de evidencia y lo pasa a RECOGIDO. Recibe: conductor_id,
    recojo_id, cantidad_declarada, lista de (bytes, nombre) por foto y la posicion GPS de la captura (C13-01)."""
    if cantidad_declarada is None or cantidad_declarada <= 0:
        raise HTTPException(status_code=400, detail="La cantidad declarada debe ser un entero mayor que 0")
    if not archivos:
        raise HTTPException(status_code=400, detail="Debes adjuntar al menos una foto de evidencia")
    if len(archivos) > settings.RECOJO_MAX_FOTOS:
        raise HTTPException(status_code=400, detail=f"Puedes adjuntar como máximo {settings.RECOJO_MAX_FOTOS} fotos")

    ruta = _ruta_recojo_activa_o_404(db, conductor_id)

    if incidencia_repository.tiene_abierta(db, ruta.id):
        raise HTTPException(status_code=400, detail="La ruta está pausada por una incidencia. Reanúdala antes de continuar.")

    recojo = recojo_repository.obtener_por_id(db, recojo_id)
    if not recojo or recojo.ruta_id != ruta.id:
        raise HTTPException(status_code=404, detail="Este recojo no pertenece a tu ruta activa")
    if recojo.estado in ESTADOS_RECOGIDO:
        raise HTTPException(status_code=400, detail="Este recojo ya fue registrado")

    # Se validan todas antes de escribir ninguna; la extension sale del contenido real.
    extensiones = [validar_imagen(contenido) for contenido, _ in archivos]

    gps = f"{latitud:.6f},{longitud:.6f}" if latitud is not None and longitud is not None else None
    os.makedirs(DIR_GUIAS, exist_ok=True)
    urls: list[str] = []
    for i, ((contenido, _), extension) in enumerate(zip(archivos, extensiones), start=1):
        # Sufijo aleatorio: /media es estatico, un nombre secuencial dejaria las
        # fotos de recojo al alcance de cualquiera que itere enteros.
        nombre_final = f"guia_{ruta.id}_{recojo_id}_{i}_{secrets.token_hex(8)}{extension}"
        with open(os.path.join(DIR_GUIAS, nombre_final), "wb") as f:
            f.write(contenido)
        url = f"/media/guias/{nombre_final}"
        urls.append(url)
        recojo_repository.agregar_evidencia(db, recojo_id, url, i, gps)

    recojo.url_guia = urls[0]  # primera foto; el resto en evidencias_recojo
    recojo.cantidad_declarada = cantidad_declarada
    recojo.estado = "RECOGIDO"
    recojo.motivo_no_realizado = None
    recojo.fecha_recojo = datetime.utcnow()

    if ruta.estado == "CREADA":
        ruta.estado = "EN_PROGRESO"

    recojo_repository.guardar_cambios(db)
    db.refresh(recojo)
    return RecepcionResponse(
        recojo_id=recojo.id, codigo=recojo.codigo, estado=recojo.estado,
        cantidad_declarada=recojo.cantidad_declarada, url_guia=recojo.url_guia, fotos=urls,
        fecha_recojo=recojo.fecha_recojo, mensaje="Recepción registrada correctamente",
    )


def marcar_no_realizado(db: Session, conductor_id: int, recojo_id: int, motivo: str) -> dict:
    """El conductor marca que no pudo hacer el recojo (tienda cerrada, sin mercaderia...) (C12-02).
    Deja de contar como pendiente; al cerrar la ruta vuelve a la lista para reprogramarlo.
    Recibe el conductor, el recojo y el motivo."""
    ruta = _ruta_recojo_activa_o_404(db, conductor_id)
    if incidencia_repository.tiene_abierta(db, ruta.id):
        raise HTTPException(status_code=400, detail="La ruta está pausada por una incidencia. Reanúdala antes de continuar.")
    recojo = recojo_repository.obtener_por_id(db, recojo_id)
    if not recojo or recojo.ruta_id != ruta.id:
        raise HTTPException(status_code=404, detail="Este recojo no pertenece a tu ruta activa")
    if recojo.estado in ESTADOS_GESTIONADOS:
        raise HTTPException(status_code=400, detail="Este recojo ya fue gestionado")
    recojo.estado = "NO_REALIZADO"
    recojo.motivo_no_realizado = motivo
    recojo.intentos_no_realizados = (recojo.intentos_no_realizados or 0) + 1
    if ruta.estado == "CREADA":
        ruta.estado = "EN_PROGRESO"
    recojo_repository.guardar_cambios(db)
    return {"recojo_id": recojo.id, "codigo": recojo.codigo, "estado": recojo.estado,
            "mensaje": "Recojo marcado como no realizado. Volverá a la lista para reprogramarlo."}


def _liberar_no_realizados(db: Session, recojos: list) -> list:
    """Devuelve a SOLICITADO (sin ruta) los recojos no realizados y avisa al admin. Recibe los recojos de la ruta."""
    liberados = [r for r in recojos if r.estado == "NO_REALIZADO"]
    for r in liberados:
        r.estado = "SOLICITADO"
        r.ruta_id = None
        r.secuencia = None
        try:
            notificaciones_service.registrar(
                db, "recojos", "Recojo no realizado",
                f"{r.codigo or r.id} · {r.cliente_origen}: {r.motivo_no_realizado or 'sin motivo'}. Volvió a la lista para reprogramarlo.",
                "/bandeja", r.id)
        except Exception:
            pass
    return liberados


def finalizar_ruta_recojo(db: Session, ruta: Ruta) -> CierreRutaResponse:
    """Cierra una ruta de recojo exigiendo que no queden recojos pendientes; los no realizados vuelven
    a la lista para reprogramarlos (C12-02). Recibe: ruta activa."""
    if incidencia_repository.tiene_abierta(db, ruta.id):
        raise HTTPException(status_code=400, detail="La ruta está pausada por una incidencia. Reanúdala antes de cerrar el día.")

    recojos = recojo_repository.obtener_por_ruta(db, ruta.id)
    pendientes = sum(1 for r in recojos if r.estado not in ESTADOS_GESTIONADOS)
    recogidas = sum(1 for r in recojos if r.estado in ESTADOS_RECOGIDO)
    if pendientes:
        raise HTTPException(status_code=400, detail=f"No puedes cerrar la ruta: quedan {pendientes} recojo(s) pendiente(s).")

    ruta.estado = "FINALIZADA"
    ruta.fecha_fin = datetime.utcnow()
    if ruta.km_estimado is None and recojos:
        primero = next((r for r in recojos if r.latitud is not None), None)
        if primero is not None:
            ruta.km_estimado = round(distancia_total(primero.latitud, primero.longitud, recojos), 2)
            ruta.km_ahorrado = 0.0
    total = len(recojos)
    liberados = _liberar_no_realizados(db, recojos)

    hora_inicio = ruta.fecha_salida or ruta.fecha_creacion
    duracion = None
    if hora_inicio:
        duracion = max(0, int((ruta.fecha_fin - hora_inicio).total_seconds() // 60))

    db.commit()
    mensaje = "Ruta de recojo finalizada correctamente"
    if liberados:
        mensaje += f". {len(liberados)} recojo(s) no realizado(s) volvieron a la lista para reprogramarlos"
    return CierreRutaResponse(
        ruta_id=ruta.id, codigo=ruta.codigo, nombre=ruta.nombre, estado=ruta.estado,
        fecha_fin=ruta.fecha_fin, hora_inicio=hora_inicio, hora_fin=ruta.fecha_fin,
        duracion_minutos=duracion, total_paradas=total, entregadas=recogidas,
        fallidas=len(liberados), pendientes=pendientes, mensaje=mensaje,
    )


def listar_rutas_recojo(db: Session, dias: int = 7) -> list[RutaRecojoItem]:
    """Rutas de recojo activas o de los ultimos dias con su avance, para el almacen (C22-02). Recibe los dias hacia atras."""
    from app.repositories import conductor_repository
    desde = datetime.utcnow() - timedelta(days=dias)
    salida = []
    for ruta in recojo_repository.listar_rutas_recojo(db, desde):
        recojos = recojo_repository.obtener_por_ruta(db, ruta.id)
        perfil = conductor_repository.obtener_perfil(db, ruta.conductor_id) if ruta.conductor_id else None
        salida.append(RutaRecojoItem(
            ruta_id=ruta.id, codigo=ruta.codigo, nombre=ruta.nombre, estado=ruta.estado,
            conductor=perfil.nombre if perfil else None, vehiculo_placa=ruta.vehiculo_placa,
            total_paradas=len(recojos),
            recogidas=sum(1 for r in recojos if r.estado in ESTADOS_RECOGIDO),
            no_realizadas=sum(1 for r in recojos if r.estado == "NO_REALIZADO"),
            fecha_creacion=ruta.fecha_creacion,
        ))
    return salida
