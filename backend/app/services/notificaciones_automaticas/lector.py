"""Lector autónomo de novedades en la base de datos (historial, rutas, incidencias, reclamos).
Corre en el contenedor notificador independiente y lee en solo lectura las tablas del núcleo
usando la tabla 'notificaciones_cursores' para garantizar que nada se duplique."""
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.repositories import notificacion_automatica_repository as repo
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

# Recojos y rutas se revisan por fecha dentro de esta ventana (cambian de estado tras crearse).
VENTANA = timedelta(days=3)


def _obtener_cursor(db: Session, fuente: str) -> int:
    """Ultimo id leido de una fuente (crea el cursor en 0 si no existe). Recibe la fuente."""
    cursor = db.query(NotificacionCursor).filter(NotificacionCursor.fuente == fuente).first()
    if not cursor:
        cursor = NotificacionCursor(fuente=fuente, ultimo_id=0)
        db.add(cursor)
        db.commit()
    return cursor.ultimo_id


def _actualizar_cursor(db: Session, fuente: str, nuevo_id: int) -> None:
    """Guarda hasta que id se leyo una fuente. Recibe la fuente y el id."""
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
    """Detecta recojos recogidos (RECOJO_COMPLETADO) e ingresos con pedidos faltantes (PAQUETES_FALTANTES).
    Un recojo cambia de estado despues de creado, por eso no sirve un cursor por id: se revisan los
    recogidos en los ultimos dias (fecha_recojo) y la clave de cada aviso evita repetirlo."""
    desde = datetime.utcnow() - VENTANA
    registros = (
        db.query(SolicitudRecojo)
        .filter(SolicitudRecojo.fecha_recojo.isnot(None), SolicitudRecojo.fecha_recojo >= desde,
                SolicitudRecojo.estado.in_(("RECOGIDO", "INGRESADO")))
        .order_by(SolicitudRecojo.id.asc())
        .limit(200)
        .all()
    )
    creados = 0
    for rec in registros:
        cliente = None
        if not repo.claves_con_prefijo(db, f"RECOJO_COMPLETADO:{rec.codigo}:"):
            cliente = db.query(ClienteCorporativo).filter(ClienteCorporativo.id == rec.cliente_id).first()
            creados += operador.registrar(db, "RECOJO_COMPLETADO", {"recojo": rec, "cliente": cliente})
        if rec.estado == "INGRESADO" and not repo.claves_con_prefijo(db, f"PAQUETES_FALTANTES:{rec.codigo}:"):
            observados = (
                db.query(Pedido.codigo)
                .filter(Pedido.recojo_id == rec.id, Pedido.estado == "OBSERVADO")
                .order_by(Pedido.id.asc())
                .all()
            )
            if observados:
                if cliente is None:
                    cliente = db.query(ClienteCorporativo).filter(ClienteCorporativo.id == rec.cliente_id).first()
                creados += operador.registrar(db, "PAQUETES_FALTANTES", {
                    "recojo": rec, "cliente": cliente, "faltantes": [c for (c,) in observados],
                })
    return creados


def barrer_rutas_finalizadas(db: Session) -> int:
    """Detecta rutas finalizadas en los ultimos dias que dejaron pedidos fallidos para retorno.
    Se usa fecha_fin (no un cursor por id: una ruta vieja puede cerrar despues que una nueva)."""
    desde = datetime.utcnow() - VENTANA
    registros = (
        db.query(Ruta)
        .filter(Ruta.estado == "FINALIZADA", Ruta.fecha_fin.isnot(None), Ruta.fecha_fin >= desde)
        .order_by(Ruta.id.asc())
        .limit(200)
        .all()
    )
    creados = 0
    for r in registros:
        if repo.existe_clave(db, f"RETORNOS_ALMACEN:{r.codigo}"):
            continue
        detalles_fallidos = (
            db.query(RutaDetalle, Pedido)
            .join(Pedido, RutaDetalle.pedido_id == Pedido.id)
            .filter(RutaDetalle.ruta_id == r.id, RutaDetalle.estado_entrega == "FALLIDO")
            .all()
        )
        if detalles_fallidos:
            fallidos = [p for _, p in detalles_fallidos]
            creados += operador.registrar(db, "RETORNOS_ALMACEN", {"ruta": r, "fallidos": fallidos})
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


def ejecutar_barrido(db: Session) -> int:
    """Ejecuta una ronda de lectura sobre todas las fuentes del núcleo. El auxilio al mecánico no se
    asigna aquí: lo confirma el administrador en Auxilio mecánico (administracion.asignar_mecanico)."""
    total = 0
    total += barrer_historial_pedidos(db)
    total += barrer_incidencias(db)
    total += barrer_proximidad_rutas_activas(db)
    total += barrer_solicitudes_recojo(db)
    total += barrer_rutas_finalizadas(db)
    total += barrer_reclamos(db)
    return total
