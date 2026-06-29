# app/services/dashboard_service.py
# La inteligencia del panel de monitoreo del admin.
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from datetime import datetime

from app.models.usuario import Usuario
from app.repositories import ruta_repository, pedido_repository, usuario_repository, historial_repository, ubicacion_repository, incidencia_repository
from app.schemas.dashboard import (
    RutaFlota,
    FlotaResponse,
    ResumenResponse,
    EventoHistorial,
    HistorialPedidoResponse,
    ClienteSeguimiento,
    ConductorUbicacion,
    ParadaMapa,
)


ESTADOS_RUTA_ACTIVA = ("CREADA", "EN_PROGRESO")
UMBRAL_EN_LINEA_SEG = 120  # un conductor está "en línea" si su última señal tiene < 2 min

# Texto legible para cada estado, usado en la línea de tiempo (CUS-35).
DESCRIPCIONES_ESTADO = {
    "POR_RECOGER": "Pendiente de recojo en el origen del cliente.",
    "OBSERVADO": "Observado en almacén: no llegó o tiene discrepancia, en espera de aclaración.",
    "LISTO_PARA_ENVIO": "Listo para envío: validado en almacén y disponible para asignar a ruta.",
    "GEOCODIFICACION_FALLIDA": "No se pudo ubicar la dirección en el mapa.",
    "ASIGNADO": "Asignado a una ruta de reparto.",
    "EN_RUTA": "En camino: el conductor optimizó la secuencia de entrega.",
    "ENTREGADO": "Paquete entregado al destinatario.",
    "FALLIDO": "Entrega fallida.",
}


def _nombre_conductor(db: Session, conductor_id) -> str | None:
    """Nombre del conductor (de su perfil) o su correo. Recibe: conductor_id o None."""
    if not conductor_id:
        return None
    from app.models.conductor import PerfilConductor
    perfil = db.query(PerfilConductor).filter(PerfilConductor.usuario_id == conductor_id).first()
    if perfil and perfil.nombre:
        return perfil.nombre
    u = usuario_repository.obtener_por_id(db, conductor_id)
    return u.correo if u else None


def _contar_estados(detalles) -> tuple[int, int, int]:
    """Cuenta (entregadas, fallidas, pendientes) a partir de los detalles de una ruta."""
    entregadas = sum(1 for d, _ in detalles if d.estado_entrega == "ENTREGADO")
    fallidas = sum(1 for d, _ in detalles if d.estado_entrega == "FALLIDO")
    pendientes = sum(1 for d, _ in detalles if d.estado_entrega == "PENDIENTE")
    return entregadas, fallidas, pendientes


# Seguimiento por cliente: agrega los pedidos por empresa y los clasifica en grupos.
def obtener_por_cliente(db: Session) -> list[ClienteSeguimiento]:
    """Agrupa los pedidos por empresa (cliente_origen) y los clasifica en
    entregados / fallidos / pendientes / en proceso. Recibe: la sesión de BD.
    Cada estado cae en exactamente un grupo, así los grupos suman el total."""
    acum: dict[str, dict] = {}
    for cliente_origen, estado, total in pedido_repository.agrupar_por_cliente(db):
        nombre = cliente_origen or "Sin cliente"
        fila = acum.setdefault(
            nombre,
            {"cliente": nombre, "total": 0, "entregados": 0, "fallidos": 0, "pendientes": 0, "en_proceso": 0},
        )
        fila["total"] += total
        if estado == "ENTREGADO":
            fila["entregados"] += total
        elif estado in ("FALLIDO", "GEOCODIFICACION_FALLIDA", "CANCELADO"):
            # CANCELADO es terminal sin entrega: se agrupa junto a fallidos (mantiene contrato suma=total).
            fila["fallidos"] += total
        elif estado in ("ASIGNADO", "EN_RUTA"):
            fila["en_proceso"] += total
        else:  # LISTO_PARA_ENVIO / POR_RECOGER / OBSERVADO / PENDIENTE (parada) y no clasificados
            fila["pendientes"] += total

    filas = sorted(acum.values(), key=lambda f: f["total"], reverse=True)
    return [ClienteSeguimiento(**f) for f in filas]


# Mapa de flota en tiempo real: posición de cada conductor activo + sus paradas pendientes.
def obtener_ubicaciones_flota(db: Session, tipo: str | None = None) -> list[ConductorUbicacion]:
    """Por cada ruta activa con conductor: su última posición conocida (con marca de
    'en línea') y las paradas aún pendientes (con coordenadas) para el mapa del panel.
    Recibe: la sesión de BD y, opcionalmente, el tipo de ruta ('RECOJO', 'ENTREGA', etc.)
    para filtrar; si tipo es None se devuelven todas las rutas activas (comportamiento original)."""
    from app.models.ruta import Ruta, RutaDetalle
    from app.models.pedido import Pedido

    ahora = datetime.utcnow()
    query = db.query(Ruta).filter(Ruta.estado.in_(ESTADOS_RUTA_ACTIVA), Ruta.conductor_id.isnot(None))
    if tipo is not None:
        query = query.filter(Ruta.tipo == tipo)
    rutas = query.all()

    # CUS-30: rutas con incidencia abierta (para marcar al conductor como pausado en el mapa).
    rutas_pausadas = incidencia_repository.rutas_con_incidencia_abierta(db)

    # Un conductor podría (excepcionalmente) tener más de una ruta activa: se agrupa
    # por conductor para NO duplicarlo en el mapa; sus paradas se fusionan.
    salida: dict[int, ConductorUbicacion] = {}
    for ruta in rutas:
        ubicacion = ubicacion_repository.obtener(db, ruta.conductor_id)
        en_linea = bool(ubicacion) and (ahora - ubicacion.actualizado_en).total_seconds() <= UMBRAL_EN_LINEA_SEG

        # Paradas pendientes de esta ruta que tengan coordenadas.
        detalles = (
            db.query(RutaDetalle, Pedido)
            .join(Pedido, RutaDetalle.pedido_id == Pedido.id)
            .filter(RutaDetalle.ruta_id == ruta.id, RutaDetalle.estado_entrega == "PENDIENTE")
            .all()
        )
        paradas = [
            ParadaMapa(
                latitud=pedido.latitud,
                longitud=pedido.longitud,
                destinatario=pedido.nombre_destinatario,
                secuencia=detalle.secuencia,
            )
            for detalle, pedido in detalles
            if pedido.latitud is not None and pedido.longitud is not None
        ]

        existente = salida.get(ruta.conductor_id)
        if existente:
            existente.paradas.extend(paradas)  # mismo conductor en otra ruta: fusiona paradas
            # CUS-30: si cualquiera de sus rutas está pausada, el conductor aparece pausado.
            existente.pausado = existente.pausado or (ruta.id in rutas_pausadas)
        else:
            salida[ruta.conductor_id] = ConductorUbicacion(
                conductor_id=ruta.conductor_id,
                conductor=_nombre_conductor(db, ruta.conductor_id),
                ruta=ruta.nombre,
                latitud=ubicacion.latitud if ubicacion else None,
                longitud=ubicacion.longitud if ubicacion else None,
                actualizado_en=ubicacion.actualizado_en if ubicacion else None,
                en_linea=en_linea,
                pausado=ruta.id in rutas_pausadas,
                paradas=paradas,
            )

    # Ordena las paradas de cada conductor por secuencia (orden de visita).
    for cu in salida.values():
        cu.paradas.sort(key=lambda p: p.secuencia if p.secuencia is not None else 0)
    return list(salida.values())


# CUS-33: Seguimiento de la flota
def obtener_flota(db: Session) -> FlotaResponse:
    """Resume el avance de TODAS las rutas para el tablero de la flota."""
    rutas = ruta_repository.listar_rutas(db)

    # Caché de nombres de conductores para no repetir consultas (evita N+1).
    cache_conductores: dict[int, str | None] = {}

    items: list[RutaFlota] = []
    for ruta in rutas:
        detalles = ruta_repository.obtener_detalles_con_pedido(db, ruta.id)
        total = len(detalles)
        entregadas, fallidas, pendientes = _contar_estados(detalles)

        # % de avance = (gestionadas / total) * 100, redondeado a 1 decimal.
        gestionadas = entregadas + fallidas
        avance = round((gestionadas / total) * 100, 1) if total else 0.0

        # Nombre del conductor (si la ruta tiene uno asignado).
        nombre = None
        if ruta.conductor_id:
            if ruta.conductor_id not in cache_conductores:
                cache_conductores[ruta.conductor_id] = _nombre_conductor(db, ruta.conductor_id)
            nombre = cache_conductores[ruta.conductor_id]

        items.append(
            RutaFlota(
                ruta_id=ruta.id,
                nombre=ruta.nombre,
                estado=ruta.estado,
                conductor_id=ruta.conductor_id,
                conductor_nombre=nombre,
                vehiculo_placa=ruta.vehiculo_placa,
                total_paradas=total,
                entregadas=entregadas,
                fallidas=fallidas,
                pendientes=pendientes,
                avance_porcentaje=avance,
                fecha_creacion=ruta.fecha_creacion,
                fecha_fin=ruta.fecha_fin,
            )
        )

    return FlotaResponse(total_rutas=len(items), rutas=items)


def obtener_resumen(db: Session) -> ResumenResponse:
    """KPIs globales: pedidos por estado y conteo de rutas (CUS-33)."""
    por_estado = {estado: total for estado, total in pedido_repository.contar_por_estado(db)}
    total_pedidos = pedido_repository.contar_total(db)

    rutas = ruta_repository.listar_rutas(db)
    activas = sum(1 for r in rutas if r.estado in ESTADOS_RUTA_ACTIVA)
    finalizadas = sum(1 for r in rutas if r.estado == "FINALIZADA")

    return ResumenResponse(
        total_pedidos=total_pedidos,
        pedidos_por_estado=por_estado,
        total_rutas=len(rutas),
        rutas_activas=activas,
        rutas_finalizadas=finalizadas,
    )


# CUS-35: Historial / línea de tiempo de un paquete
def obtener_historial(db: Session, codigo: str) -> HistorialPedidoResponse:
    """
    CUS-35: línea de tiempo REAL de un paquete (por su código PD-001), leída de
    la tabla 'historial_pedidos' (cada cambio quedó registrado con fecha y
    usuario). Se complementa con datos de la ruta y la evidencia.
    """
    pedido = pedido_repository.obtener_por_codigo(db, codigo)
    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe un pedido con código '{codigo}'",
        )

    # Eventos reales registrados, en orden cronológico.
    registros = historial_repository.listar_por_pedido(db, pedido.id)
    cache_correos: dict[int, str] = {}

    eventos: list[EventoHistorial] = []
    for r in registros:
        correo = None
        if r.usuario_id:
            if r.usuario_id not in cache_correos:
                u = usuario_repository.obtener_por_id(db, r.usuario_id)
                cache_correos[r.usuario_id] = u.correo if u else None
            correo = cache_correos[r.usuario_id]

        eventos.append(EventoHistorial(
            evento=r.estado_nuevo,
            descripcion=DESCRIPCIONES_ESTADO.get(r.estado_nuevo, "Cambio de estado."),
            fecha=r.fecha_utc,
            realizado_por=correo,
        ))

    # Datos complementarios desde la ruta/detalle (evidencia, motivo, parada).
    ruta_nombre = None
    conductor_nombre = None
    secuencia = None
    url_evidencia = None
    motivo_fallo = None

    par = ruta_repository.obtener_detalle_y_ruta_por_pedido(db, pedido.id)
    if par:
        detalle, ruta = par
        ruta_nombre = ruta.nombre
        secuencia = detalle.secuencia
        url_evidencia = detalle.url_evidencia
        motivo_fallo = detalle.motivo_fallo
        conductor_nombre = _nombre_conductor(db, ruta.conductor_id)

    return HistorialPedidoResponse(
        codigo=pedido.codigo,
        cliente_origen=pedido.cliente_origen,
        direccion_destino=pedido.direccion_destino,
        distrito=pedido.distrito,
        estado_actual=pedido.estado,
        ruta_asignada=ruta_nombre,
        conductor_asignado=conductor_nombre,
        secuencia=secuencia,
        url_evidencia=url_evidencia,
        motivo_fallo=motivo_fallo,
        eventos=eventos,
    )


def obtener_eficiencia_conductores(db: Session) -> list[dict]:
    """CUS-34: por cada conductor activo, suma los km de sus rutas YA cerradas
    (fecha_fin no nula) y calcula el ahorro de combustible con los parámetros
    administrables. Acumulado (no solo hoy). Recibe: la sesión de BD."""
    from app.models.ruta import Ruta
    from app.services import parametro_service

    combustible = parametro_service.obtener_combustible(db)
    consumo = combustible["consumo_l_100km"]
    precio = combustible["precio_soles_litro"]

    # Sumas de km por conductor en una sola consulta (rutas cerradas con conductor).
    filas = (
        db.query(
            Ruta.conductor_id,
            func.coalesce(func.sum(Ruta.km_estimado), 0.0),
            func.coalesce(func.sum(Ruta.km_ahorrado), 0.0),
        )
        .filter(Ruta.fecha_fin.isnot(None), Ruta.conductor_id.isnot(None))
        .group_by(Ruta.conductor_id)
        .all()
    )
    sumas = {cid: (float(km_e or 0.0), float(km_a or 0.0)) for cid, km_e, km_a in filas}

    # Lista de conductores activos (aunque no tengan rutas cerradas -> 0).
    conductores = (
        db.query(Usuario)
        .filter(Usuario.rol == "conductor", Usuario.estado == True)  # noqa: E712
        .all()
    )
    resultado = []
    for u in conductores:
        km_recorridos, km_ahorrados = sumas.get(u.id, (0.0, 0.0))
        litros = km_ahorrados * (consumo / 100.0)
        resultado.append({
            "conductor_id": u.id,
            "nombre": _nombre_conductor(db, u.id),
            "km_recorridos": round(km_recorridos, 2),
            "km_ahorrados": round(km_ahorrados, 2),
            "litros_ahorrados": round(litros, 2),
            "soles_ahorrados": round(litros * precio, 2),
        })
    return resultado
