# Metricas del asistente de atencion para la pantalla de administracion. Solo cuenta lo que ya
# guardan las tablas propias (ya enmascaradas): nunca lee datos del nucleo. Los volumenes son
# chicos (las conversaciones se borran a los 30 dias), asi que se agrupa en Python y la misma
# consulta sirve en PostgreSQL y en SQLite (pruebas).
from collections import Counter
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.fechas import ahora_utc
from app.models.conversacion import Conversacion, Mensaje
from app.models.gestion import Accion, Derivacion


def _dia_local(momento: datetime) -> str:
    """Fecha local (Lima) AAAA-MM-DD de una marca UTC sin zona. Recibe la marca."""
    return momento.replace(tzinfo=timezone.utc).astimezone(ZoneInfo(settings.ZONA_HORARIA)).strftime("%Y-%m-%d")


def metricas(db: Session, dias: int, titulos: dict[str, str]) -> dict:
    """Resumen de los ultimos dias. Recibe la sesion, cuantos dias y los titulos de los articulos por clave."""
    desde = ahora_utc() - timedelta(days=dias)
    conversaciones = db.execute(select(Conversacion.id, Conversacion.creada_en, Conversacion.idioma, Conversacion.pagina)
                                .where(Conversacion.creada_en >= desde, Conversacion.mensajes_usuario > 0)).all()
    ids = {c.id for c in conversaciones}
    derivadas = set(db.execute(select(Derivacion.conversacion_id).where(Derivacion.creada_en >= desde)).scalars().all())
    respuestas = db.execute(select(Mensaje.modo, Mensaje.proveedor, Mensaje.articulos, Mensaje.creado_en)
                            .where(Mensaje.rol == "asistente", Mensaje.creado_en >= desde)).all()
    alertas = db.execute(select(Mensaje.id).where(Mensaje.rol == "usuario", Mensaje.creado_en >= desde,
                                                  Mensaje.alerta_seguridad.is_not(None))).all()
    voz = db.execute(select(Mensaje.id).where(Mensaje.rol == "usuario", Mensaje.creado_en >= desde,
                                              Mensaje.origen == "voz")).all()
    acciones = db.execute(select(Accion.tipo, Accion.estado).where(Accion.creada_en >= desde)).all()
    pendientes = db.execute(select(Derivacion.id).where(Derivacion.estado == "PENDIENTE")).all()

    total = len(ids)
    sin_humano = len(ids - derivadas)
    temas = Counter(clave for r in respuestas for clave in (r.articulos or []))
    por_dia = Counter(_dia_local(c.creada_en) for c in conversaciones)
    estados_acciones = Counter((a.tipo, a.estado) for a in acciones)
    return {
        "dias": dias,
        "conversaciones": total,
        "resueltas_sin_persona": sin_humano,
        "porcentaje_sin_persona": round(100 * sin_humano / total, 1) if total else None,
        "derivadas": len(ids & derivadas),
        "derivaciones_pendientes": len(pendientes),
        "empresas_captadas": estados_acciones[("contacto", "CONFIRMADA")],
        "reprogramaciones": estados_acciones[("reprogramar", "CONFIRMADA")],
        "propuestas": len(acciones),
        "mensajes_por_voz": len(voz),
        "alertas_seguridad": len(alertas),
        "respuestas_por_modo": dict(Counter(r.modo or "ia" for r in respuestas)),
        "temas": [{"clave": k, "titulo": titulos.get(k, k), "veces": n} for k, n in temas.most_common(8)],
        # Metricas avanzadas (se recortan primero si falta tiempo): serie diaria, idiomas, paginas, proveedores.
        "por_dia": [{"dia": d, "conversaciones": por_dia[d]} for d in sorted(por_dia)],
        "por_idioma": dict(Counter(c.idioma for c in conversaciones)),
        "por_pagina": dict(Counter(c.pagina for c in conversaciones)),
        "por_proveedor": dict(Counter(r.proveedor for r in respuestas if r.proveedor)),
    }
