# Politica de retencion de datos del destinatario (EX-04): pasado el plazo que fija la gerencia
# (por defecto 6 meses desde la entrega o cancelacion), se retiran nombre, telefono, DNI, direccion
# exacta, coordenadas y los datos de quien recibio. Quedan el codigo, el cliente, el distrito, las
# fechas y el historial, que bastan para los indicadores. El Libro de Reclamaciones no se toca
# (tiene su propio plazo legal de conservacion).
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.registro import obtener_logger
from app.models.evidencia import EvidenciaEntrega
from app.models.pedido import Pedido
from app.repositories import parametro_repository

CATEGORIA = "privacidad"
CLAVE_MESES = "retencion_meses"
MESES_DEFECTO = 6
ESTADOS_CERRADOS = ("ENTREGADO", "CANCELADO")
TANDA = 500
_log = obtener_logger("privacidad")


def obtener_config(db: Session) -> dict:
    """Meses de retencion configurados (0 = no se retiran datos). Recibe la sesion."""
    filas = {p.clave: p.valor_json for p in parametro_repository.listar_por_categoria(db, CATEGORIA)}
    meses = filas.get(CLAVE_MESES, MESES_DEFECTO)
    return {"retencion_meses": meses if isinstance(meses, int) and meses >= 0 else MESES_DEFECTO}


def actualizar_config(db: Session, meses: int) -> dict:
    """Guarda los meses de retencion (0 a 120). Recibe la sesion y los meses."""
    if not 0 <= meses <= 120:
        raise HTTPException(status_code=400, detail="Los meses de retención deben estar entre 0 y 120")
    parametro_repository.fijar_valor(db, CATEGORIA, CLAVE_MESES, int(meses))
    return obtener_config(db)


def iniciales(nombre: str | None) -> str | None:
    """Deja solo las iniciales de un nombre ("Luis Rojas" -> "L. R."). Recibe el nombre."""
    partes = [p for p in (nombre or "").split() if p]
    return " ".join(f"{p[0].upper()}." for p in partes[:3]) or None


def _retirar(pedido, evidencia, ahora) -> None:
    """Quita los datos personales de un pedido y de su evidencia. Recibe el pedido, su evidencia y la hora."""
    pedido.nombre_destinatario = iniciales(pedido.nombre_destinatario)
    pedido.telefono_destinatario = None
    pedido.dni_destinatario = None
    pedido.direccion_destino = f"Dirección retirada por antigüedad{f' · {pedido.distrito}' if pedido.distrito else ''}"
    pedido.latitud = None
    pedido.longitud = None
    pedido.datos_retirados_en = ahora
    if evidencia:
        evidencia.receptor_nombre = iniciales(evidencia.receptor_nombre)
        evidencia.receptor_documento = None
        evidencia.latitud_longitud_captura = None


def aplicar_retencion(db: Session, ahora: datetime | None = None) -> dict:
    """Retira los datos personales de los pedidos cerrados hace mas de N meses (por tandas). Recibe la sesion.
    Devuelve cuantos pedidos se procesaron."""
    meses = obtener_config(db)["retencion_meses"]
    if meses == 0:
        return {"pedidos": 0, "retencion_meses": 0}
    ahora = ahora or datetime.utcnow()
    limite = ahora - timedelta(days=30 * meses)
    total = 0
    while True:
        tanda = (
            db.query(Pedido)
            .filter(
                Pedido.estado.in_(ESTADOS_CERRADOS),
                Pedido.datos_retirados_en.is_(None),
                Pedido.fecha_creacion < limite,
                (Pedido.fecha_entrega.is_(None)) | (Pedido.fecha_entrega < limite),
            )
            .order_by(Pedido.id)
            .limit(TANDA)
            .all()
        )
        if not tanda:
            break
        evidencias = {
            e.pedido_id: e
            for e in db.query(EvidenciaEntrega).filter(EvidenciaEntrega.pedido_id.in_([p.id for p in tanda])).all()
        }
        for pedido in tanda:
            _retirar(pedido, evidencias.get(pedido.id), ahora)
        db.commit()
        total += len(tanda)
    if total:
        _log.info("Retención: se retiraron los datos personales de %s pedidos (más de %s meses)", total, meses)
    return {"pedidos": total, "retencion_meses": meses}
