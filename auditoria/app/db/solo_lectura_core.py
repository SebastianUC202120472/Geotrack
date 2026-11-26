from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.registro import obtener_logger

_log = obtener_logger("solo_lectura_core")

# Subconsulta compatible con PostgreSQL y SQLite que toma únicamente el último
# detalle de ruta por pedido (evita filas duplicadas cuando un pedido fallido se reasigna).
_BASE_SELECT_EVIDENCIA = """
    SELECT
        e.id AS evidencia_id,
        e.pedido_id,
        e.url_foto,
        e.url_firma,
        e.latitud_longitud_captura,
        e.receptor_nombre,
        e.receptor_documento,
        e.fecha_hora AS fecha_entrega,
        p.codigo AS pedido_codigo,
        p.direccion_destino,
        p.distrito AS pedido_distrito,
        p.latitud AS pedido_latitud,
        p.longitud AS pedido_longitud,
        p.estado AS pedido_estado,
        rd.ruta_id,
        r.conductor_id,
        u.nombre AS conductor_nombre,
        u.correo AS conductor_correo
    FROM evidencias_entrega e
    JOIN pedidos p ON e.pedido_id = p.id
    LEFT JOIN (
        SELECT pedido_id, MAX(id) AS ultimo_rd_id
        FROM ruta_detalles
        GROUP BY pedido_id
    ) ult ON ult.pedido_id = p.id
    LEFT JOIN ruta_detalles rd ON rd.id = ult.ultimo_rd_id
    LEFT JOIN rutas r ON rd.ruta_id = r.id
    LEFT JOIN usuarios u ON r.conductor_id = u.id
"""


def _normalizar_fila(fila: Dict[str, Any]) -> Dict[str, Any]:
    """Convierte timestamps string (SQLite) a datetime para mantener paridad con PostgreSQL."""
    valor = fila.get("fecha_entrega")
    if isinstance(valor, str):
        try:
            fila["fecha_entrega"] = datetime.fromisoformat(valor)
        except ValueError:
            fila["fecha_entrega"] = None
    return fila


def obtener_evidencias_recientes(db: Session, limite: int = 100) -> List[Dict[str, Any]]:
    """Consulta evidencias de entrega con foto en modo solo lectura sobre el esquema público."""
    consulta = text(
        _BASE_SELECT_EVIDENCIA
        + """
        WHERE e.url_foto IS NOT NULL AND e.url_foto != ''
        ORDER BY e.id DESC
        LIMIT :limite
        """
    )
    filas = db.execute(consulta, {"limite": limite}).mappings().all()
    return [_normalizar_fila(dict(f)) for f in filas]


def obtener_evidencia_por_id(db: Session, evidencia_id: int) -> Optional[Dict[str, Any]]:
    """Obtiene el detalle completo de una evidencia de entrega por su ID (solo lectura)."""
    consulta = text(
        _BASE_SELECT_EVIDENCIA
        + """
        WHERE e.id = :evidencia_id
        LIMIT 1
        """
    )
    fila = db.execute(consulta, {"evidencia_id": evidencia_id}).mappings().first()
    return _normalizar_fila(dict(fila)) if fila else None


def buscar_reclamos_por_pedido(db: Session, pedido_codigo: str) -> List[Dict[str, Any]]:
    """Consulta en solo lectura si existen reclamos registrados para este código de pedido."""
    if not pedido_codigo:
        return []
    consulta = text("""
        SELECT
            id,
            codigo,
            tipo,
            detalle,
            creado_en
        FROM reclamos
        WHERE pedido_codigo = :codigo
        ORDER BY id DESC
    """)
    try:
        filas = db.execute(consulta, {"codigo": pedido_codigo}).mappings().all()
        return [dict(f) for f in filas]
    except Exception as e:
        _log.warning("No se pudo consultar reclamos para el pedido %s: %s", pedido_codigo, e)
        return []


def obtener_mapa_evidencias_por_ids(db: Session, evidencia_ids: List[int]) -> Dict[int, Dict[str, Any]]:
    """Obtiene en lote (solo lectura) los datos de pedido y conductor para una lista de evidencias."""
    if not evidencia_ids:
        return {}
    ids_limpios = [int(i) for i in evidencia_ids]
    placeholders = ", ".join(f":id_{idx}" for idx in range(len(ids_limpios)))
    params = {f"id_{idx}": val for idx, val in enumerate(ids_limpios)}
    consulta = text(
        _BASE_SELECT_EVIDENCIA
        + f" WHERE e.id IN ({placeholders})"
    )
    filas = db.execute(consulta, params).mappings().all()
    return {f["evidencia_id"]: _normalizar_fila(dict(f)) for f in filas}


def obtener_conteo_reclamos_por_pedidos(db: Session, codigos_pedido: List[str]) -> Dict[str, int]:
    """Devuelve {pedido_codigo: cantidad_reclamos} en solo lectura."""
    codigos = list({c for c in codigos_pedido if c})
    if not codigos:
        return {}
    placeholders = ", ".join(f":cod_{idx}" for idx in range(len(codigos)))
    params = {f"cod_{idx}": val for idx, val in enumerate(codigos)}
    consulta = text(f"""
        SELECT pedido_codigo, COUNT(*) AS total
        FROM reclamos
        WHERE pedido_codigo IN ({placeholders})
        GROUP BY pedido_codigo
    """)
    try:
        filas = db.execute(consulta, params).mappings().all()
        return {f["pedido_codigo"]: int(f["total"]) for f in filas}
    except Exception as e:
        _log.warning("No se pudo consultar conteo de reclamos en lote: %s", e)
        return {}
