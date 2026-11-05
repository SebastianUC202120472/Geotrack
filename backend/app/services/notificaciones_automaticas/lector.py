"""Lector autónomo de novedades en la base de datos (historial, rutas, incidencias, reclamos).
Corre en el contenedor notificador independiente y lee en solo lectura las tablas del núcleo
usando la tabla 'notificaciones_cursores' para garantizar que nada se duplique."""
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.historial import HistorialPedido
from app.models.pedido import Pedido
from app.models.ruta import Ruta, RutaDetalle
from app.models.incidencia import Incidencia
from app.models.solicitud_recojo import SolicitudRecojo
from app.models.cliente import ClienteCorporativo
from app.models.reclamo import Reclamo
from app.models.notificacion_cursor import NotificacionCursor
from app.services.notificaciones_automaticas import operador

log = logging.getLogger("geotrack.notificador.lector")


def _obtener_cursor(db: Session, fuente: str) -> int:
    cursor = db.query(NotificacionCursor).filter(NotificacionCursor.fuente == fuente).first()
    if not cursor:
        cursor = NotificacionCursor(fuente=fuente, ultimo_id=0)
        db.add(cursor)
        db.commit()
    return cursor.ultimo_id


def _actualizar_cursor(db: Session, fuente: str, nuevo_id: int) -> None:
    cursor = db.query(NotificacionCursor).filter(NotificacionCursor.fuente == fuente).first()
    if cursor:
        cursor.ultimo_id = nuevo_id
        cursor.actualizado_en = datetime.utcnow()
        db.commit()


def barrer_historial_pedidos(db: Session) -> int:
    """Detecta cambios de estado en pedidos: ASIGNADO, EN_RUTA, ENTREGADO, FALLIDO, LISTO_PARA_ENVIO (reprogramado)."""
    ultimo_id = _obtener_cursor(db, "historial_pedidos")
    registros = (
        db.query(HistorialPedido)
        .filter(HistorialPedido.id > ultimo_id)
        .order_by(HistorialPedido.id.asc())
        .limit(100)
        .all()
    )
    if not registros:
        return 0

    max_id = ultimo_id
    creados = 0
    for h in registros:
        max_id = max(max_id, h.id)
        pedido = db.query(Pedido).filter(Pedido.id == h.pedido_id).first()
        if not pedido:
            continue

        # Obtener detalle de ruta si aplica
        detalle = (
            db.query(RutaDetalle)
            .filter(RutaDetalle.pedido_id == pedido.id)
            .order_by(RutaDetalle.id.desc())
            .first()
        )
        ruta_id = detalle.ruta_id if detalle else 0

        if h.estado_nuevo == "ASIGNADO":
            creados += operador.registrar(
                db, "PEDIDO_PROGRAMADO", {"pedido": pedido, "ocurrencia": f"R{ruta_id}"}
            )
        elif h.estado_nuevo == "EN_RUTA":
            total = db.query(RutaDetalle).filter(RutaDetalle.ruta_id == ruta_id).count() if ruta_id else 1
            secuencia = detalle.secuencia if detalle else 1
            creados += operador.registrar(
                db, "PEDIDO_EN_CAMINO", {
                    "pedido": pedido,
                    "secuencia": secuencia,
                    "total": total,
                    "ocurrencia": f"R{ruta_id}"
                }
            )
        elif h.estado_nuevo == "ENTREGADO":
            creados += operador.registrar(
                db, "PEDIDO_ENTREGADO", {"pedido": pedido, "ocurrencia": f"R{ruta_id}"}
            )
        elif h.estado_nuevo == "FALLIDO":
            motivo = detalle.motivo_fallo if detalle else "Destinatario ausente"
            creados += operador.registrar(
                db, "PEDIDO_NO_ENTREGADO", {
                    "pedido": pedido,
                    "motivo": motivo,
                    "ocurrencia": f"R{ruta_id}"
                }
            )
        elif h.estado_nuevo == "LISTO_PARA_ENVIO" and h.estado_anterior in ("FALLIDO", "OBSERVADO"):
            creados += operador.registrar(
                db, "PEDIDO_REPROGRAMADO", {"pedido": pedido, "ocurrencia": f"H{h.id}"}
            )

    _actualizar_cursor(db, "historial_pedidos", max_id)
    return creados


def barrer_incidencias(db: Session) -> int:
    """Detecta nuevas averías mecánicas reportadas por conductores."""
    ultimo_id = _obtener_cursor(db, "incidencias")
    registros = (
        db.query(Incidencia)
        .filter(Incidencia.id > ultimo_id)
        .order_by(Incidencia.id.asc())
        .limit(50)
        .all()
    )
    if not registros:
        return 0

    max_id = ultimo_id
    creados = 0
    for inc in registros:
        max_id = max(max_id, inc.id)
        if inc.tipo == "AVERIA_MECANICA":
            ruta = db.query(Ruta).filter(Ruta.id == inc.ruta_id).first()
            creados += operador.registrar(db, "AUXILIO_MECANICO", {"incidencia": inc, "ruta": ruta})

    _actualizar_cursor(db, "incidencias", max_id)
    return creados


def barrer_solicitudes_recojo(db: Session) -> int:
    """Detecta recojos completados (RECOGIDO) o ingresados a almacén con faltantes."""
    ultimo_id = _obtener_cursor(db, "solicitudes_recojo")
    registros = (
        db.query(SolicitudRecojo)
        .filter(SolicitudRecojo.id > ultimo_id)
        .order_by(SolicitudRecojo.id.asc())
        .limit(50)
        .all()
    )
    if not registros:
        return 0

    max_id = ultimo_id
    creados = 0
    for rec in registros:
        max_id = max(max_id, rec.id)
        cliente = db.query(ClienteCorporativo).filter(ClienteCorporativo.id == rec.cliente_id).first()
        if rec.estado == "RECOGIDO":
            creados += operador.registrar(db, "RECOJO_COMPLETADO", {"recojo": rec, "cliente": cliente})
        elif rec.estado == "INGRESADO" and rec.intentos_no_realizados and rec.intentos_no_realizados > 0:
            # Observado con faltantes
            creados += operador.registrar(
                db, "PAQUETES_FALTANTES", {
                    "recojo": rec,
                    "cliente": cliente,
                    "faltantes": [f"Bultos no conformes ({rec.intentos_no_realizados})"]
                }
            )

    _actualizar_cursor(db, "solicitudes_recojo", max_id)
    return creados


def barrer_rutas_finalizadas(db: Session) -> int:
    """Detecta rutas que acaban de finalizar y evalúa si dejaron retornos de pedidos fallidos."""
    ultimo_id = _obtener_cursor(db, "rutas")
    registros = (
        db.query(Ruta)
        .filter(Ruta.id > ultimo_id, Ruta.estado == "FINALIZADA")
        .order_by(Ruta.id.asc())
        .limit(50)
        .all()
    )
    if not registros:
        return 0

    max_id = ultimo_id
    creados = 0
    for r in registros:
        max_id = max(max_id, r.id)
        detalles_fallidos = (
            db.query(RutaDetalle, Pedido)
            .join(Pedido, RutaDetalle.pedido_id == Pedido.id)
            .filter(RutaDetalle.ruta_id == r.id, RutaDetalle.estado_entrega == "FALLIDO")
            .all()
        )
        if detalles_fallidos:
            fallidos = [p for _, p in detalles_fallidos]
            creados += operador.registrar(db, "RETORNOS_ALMACEN", {"ruta": r, "fallidos": fallidos})

    _actualizar_cursor(db, "rutas", max_id)
    return creados


def barrer_reclamos(db: Session) -> int:
    """Detecta nuevos reclamos registrados en el Libro de Reclamaciones."""
    ultimo_id = _obtener_cursor(db, "reclamos")
    registros = (
        db.query(Reclamo)
        .filter(Reclamo.id > ultimo_id)
        .order_by(Reclamo.id.asc())
        .limit(50)
        .all()
    )
    if not registros:
        return 0

    max_id = ultimo_id
    creados = 0
    for rec in registros:
        max_id = max(max_id, rec.id)
        creados += operador.registrar(db, "RECLAMO_NUEVO", {"reclamo": rec})

    _actualizar_cursor(db, "reclamos", max_id)
    return creados


def barrer_proximidad_rutas_activas(db: Session) -> int:
    """Evalúa de forma autónoma la proximidad del conductor a las paradas en rutas activas."""
    from app.services.notificaciones_automaticas.proximidad import evaluar_proximidad
    rutas_activas = db.query(Ruta).filter(Ruta.estado == "EN_PROGRESO", Ruta.conductor_id.isnot(None)).all()
    creados = 0
    for r in rutas_activas:
        creados += evaluar_proximidad(db, r.id, r.conductor_id)
    return creados


def barrer_ayudas_asignadas(db: Session) -> int:
    """Detecta incidencias donde se mandó ayuda y dispara el aviso AYUDA_ASIGNADA al mecánico propuesto."""
    from app.models.conductor import PerfilConductor
    from app.models.notificacion_mecanico import NotificacionMecanico
    from app.models.notificacion_envio import NotificacionEnvio
    from app.services.router import calcular_distancia

    incidencias = (
        db.query(Incidencia)
        .filter(Incidencia.estado == "ABIERTA", Incidencia.ayuda_enviada_en.isnot(None))
        .all()
    )
    creados = 0
    for inc in incidencias:
        prefijo = f"AYUDA_ASIGNADA:{inc.codigo}:"
        ya_enviado = (
            db.query(NotificacionEnvio)
            .filter(NotificacionEnvio.clave_idempotencia.like(f"{prefijo}%"))
            .first()
        )
        if ya_enviado:
            continue

        mecanicos = (
            db.query(NotificacionMecanico)
            .filter(NotificacionMecanico.activo.is_(True), NotificacionMecanico.telefono_verificado.is_(True))
            .all()
        )
        if not mecanicos:
            continue

        lat_inc, lon_inc = inc.latitud, inc.longitud
        candidatos = []
        for m in mecanicos:
            dist = 999.0
            if lat_inc is not None and lon_inc is not None and m.latitud is not None and m.longitud is not None:
                dist = calcular_distancia(lat_inc, lon_inc, m.latitud, m.longitud)
            candidatos.append((dist, m))
        candidatos.sort(key=lambda x: x[0])
        mejor_mecanico = candidatos[0][1]

        perfil = db.query(PerfilConductor).filter(PerfilConductor.usuario_id == inc.conductor_id).first()
        conductor_nombre = perfil.nombre if perfil else "Conductor"
        conductor_tel = perfil.telefono if perfil else ""

        creados += operador.registrar(
            db, "AYUDA_ASIGNADA", {
                "incidencia": inc,
                "mecanico_id": mejor_mecanico.id,
                "mecanico_nombre": mejor_mecanico.nombre,
                "mecanico_chat_id": mejor_mecanico.telegram_chat_id,
                "conductor_nombre": conductor_nombre,
                "conductor_telefono": conductor_tel,
            }
        )
    return creados


def ejecutar_barrido(db: Session) -> int:
    """Ejecuta una ronda de lectura sobre todas las fuentes del núcleo."""
    total = 0
    total += barrer_historial_pedidos(db)
    total += barrer_incidencias(db)
    total += barrer_ayudas_asignadas(db)
    total += barrer_proximidad_rutas_activas(db)
    total += barrer_solicitudes_recojo(db)
    total += barrer_rutas_finalizadas(db)
    total += barrer_reclamos(db)
    return total
