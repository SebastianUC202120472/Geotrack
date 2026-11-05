"""Planificador de tareas periódicas:
1. Horario silencioso (21:00 - 08:00 America/Lima).
2. Resumen diario a las 20:00 America/Lima para clientes corporativos.
3. Recordatorio legal de reclamos (a los 12 días sin resolución).
"""
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.cliente import ClienteCorporativo
from app.models.pedido import Pedido
from app.models.reclamo import Reclamo
from app.models.notificacion_envio import NotificacionEnvio
from app.services.notificaciones_automaticas import operador
from app.services.notificaciones_automaticas.modelos import Prioridad

log = logging.getLogger("geotrack.notificador.planificador")


def en_horario_silencioso(ahora_dt: datetime | None = None) -> bool:
    """Devuelve True si la hora actual en la zona horaria oficial está entre 21:00 y 08:00."""
    try:
        tz = ZoneInfo(settings.ZONA_HORARIA or "America/Lima")
    except Exception:
        tz = ZoneInfo("America/Lima")

    ahora = ahora_dt.astimezone(tz) if ahora_dt else datetime.now(tz)
    hora = ahora.hour
    return hora >= 21 or hora < 8


def ejecutar_resumen_diario(db: Session, ahora_dt: datetime | None = None) -> int:
    """A las 20:00 (en ventana 20:00-20:59) agrupa y despacha el resumen del día a clientes corporativos."""
    try:
        tz = ZoneInfo(settings.ZONA_HORARIA or "America/Lima")
    except Exception:
        tz = ZoneInfo("America/Lima")

    ahora = ahora_dt.astimezone(tz) if ahora_dt else datetime.now(tz)
    if ahora.hour != 20:
        return 0

    fecha_str = ahora.strftime("%Y-%m-%d")
    inicio_dia = datetime(ahora.year, ahora.month, ahora.day)

    clientes = db.query(ClienteCorporativo).filter(ClienteCorporativo.acceso_activo.is_(True)).all()
    creados = 0
    for cliente in clientes:
        pedidos_hoy = (
            db.query(Pedido)
            .filter(Pedido.cliente_id == cliente.id, Pedido.fecha_creacion >= inicio_dia)
            .all()
        )
        if not pedidos_hoy:
            continue

        conteos = {
            "entregados": sum(1 for p in pedidos_hoy if p.estado == "ENTREGADO"),
            "fallidos": sum(1 for p in pedidos_hoy if p.estado == "FALLIDO"),
            "pendientes": sum(1 for p in pedidos_hoy if p.estado not in ("ENTREGADO", "FALLIDO", "CANCELADO")),
        }
        creados += operador.registrar(
            db, "RESUMEN_DEL_DIA", {
                "cliente": cliente,
                "fecha": fecha_str,
                "conteos": conteos,
            }
        )
    return creados


def evaluar_reclamos_por_vencer(db: Session, ahora_dt: datetime | None = None) -> int:
    """Revisa reclamos con 12 días calendario (plazo legal 15 días hábiles) y avisa al admin."""
    ahora = ahora_dt or datetime.utcnow()
    reclamos = db.query(Reclamo).all()
    creados = 0
    for r in reclamos:
        if not r.creado_en:
            continue
        dias = (ahora - r.creado_en).days
        if dias >= 12:
            clave = f"RECLAMO_VENCE:{r.codigo}"
            ya_existe = db.query(NotificacionEnvio).filter(NotificacionEnvio.clave_idempotencia == clave).first()
            if not ya_existe:
                asunto = f"ALERTA: Plazo legal por vencer — Reclamo {r.codigo}"
                cuerpo = (
                    f"El {r.tipo.lower()} {r.codigo} lleva {dias} días sin atender.\n"
                    f"Consumidor: {r.consumidor_nombre}\n"
                    f"Plazo legal máximo de respuesta: 15 días hábiles (Ley 29571)."
                )
                from app.services.notificaciones_automaticas.constructor import _correo
                from app.services.notificaciones_automaticas import destinatarios as dest
                msg = _correo(
                    "RECLAMO_NUEVO", "administrador", dest.email_admin(),
                    asunto, cuerpo, clave, prioridad=Prioridad.URGENTE
                )
                if msg:
                    from app.repositories import notificacion_envio_repository
                    if notificacion_envio_repository.crear_si_no_existe(db, msg):
                        creados += 1
                        db.commit()
    return creados


def evaluar_timeout_mecanicos(db: Session, ahora_dt: datetime | None = None) -> int:
    """Si el mecánico asignado no responde 'VOY' en 10 minutos, avisa al administrador para proponer al siguiente."""
    from datetime import timedelta
    from app.models.incidencia import Incidencia
    from app.services.notificaciones_automaticas.constructor import _correo
    from app.services.notificaciones_automaticas import destinatarios as dest
    from app.repositories import notificacion_envio_repository

    ahora = ahora_dt or datetime.utcnow()
    limite = ahora - timedelta(minutes=10)

    # Incidencias abiertas donde se envió ayuda hace más de 10 min y no se ha resuelto
    incidencias = (
        db.query(Incidencia)
        .filter(
            Incidencia.estado == "ABIERTA",
            Incidencia.ayuda_enviada_en.isnot(None),
            Incidencia.ayuda_enviada_en <= limite,
        )
        .all()
    )

    creados = 0
    for inc in incidencias:
        clave = f"TIMEOUT_MECANICO:{inc.codigo}:{inc.ayuda_enviada_en.strftime('%Y%m%d%H%M')}"
        ya_notificado = db.query(NotificacionEnvio).filter(NotificacionEnvio.clave_idempotencia == clave).first()
        if not ya_notificado:
            asunto = f"URGENTE: Mecánico no responde a auxilio {inc.codigo} (10 min)"
            cuerpo = (
                f"El auxilio {inc.codigo} para el vehículo {inc.vehiculo_placa or 'sin placa'} "
                f"lleva más de 10 minutos sin confirmación 'VOY'.\n"
                f"Ingresa a Auxilio Mecánico para reasignar al siguiente proveedor más cercano."
            )
            msg = _correo(
                "AUXILIO_MECANICO", "administrador", dest.email_admin(),
                asunto, cuerpo, clave, prioridad=Prioridad.URGENTE
            )
            if msg and notificacion_envio_repository.crear_si_no_existe(db, msg):
                creados += 1
                db.commit()
    return creados
