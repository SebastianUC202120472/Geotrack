"""Evalua la proximidad del conductor a las paradas para el aviso 'Esta cerca'."""
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.notificacion_envio import NotificacionEnvio
from app.repositories import ruta_repository, ubicacion_repository
from app.services.router import calcular_distancia
from app.services.notificaciones_automaticas import operador
from app.services.notificaciones_automaticas.constructor import clave_pedido

# Umbral en km para considerar que el repartidor esta cerca de una parada.
UMBRAL_CERCA_KM = 2.0
EVENTO = "PEDIDO_ESTA_CERCA"


def evaluar_proximidad(db: Session, ruta_id: int, conductor_id: int) -> int:
    """Crea el aviso para las paradas proximas; devuelve cuantos creo (no duplica).
    Se llama en cada actualizacion de ubicacion: con el modulo apagado no consulta nada, y
    descarta de antemano los pedidos que ya tienen su aviso para no reconstruirlos."""
    if not settings.NOTIFICACIONES_HABILITADAS:
        return 0

    detalles = ruta_repository.obtener_detalles_con_pedido(db, ruta_id)
    pendientes = sorted(
        [(detalle.secuencia, pedido) for detalle, pedido in detalles
         if detalle.estado_entrega == "PENDIENTE" and pedido.latitud is not None],
        key=lambda x: x[0] or 0,
    )
    if not pendientes:
        return 0

    ocurrencia = f"R{ruta_id}"
    claves = {clave_pedido(EVENTO, p, ocurrencia) for _, p in pendientes}
    ya_avisados = {
        c for (c,) in db.query(NotificacionEnvio.clave_idempotencia)
        .filter(NotificacionEnvio.clave_idempotencia.in_(claves))
        .all()
    }

    ubicacion = ubicacion_repository.obtener(db, conductor_id)
    creados = 0
    for indice, (_, pedido) in enumerate(pendientes):
        if clave_pedido(EVENTO, pedido, ocurrencia) in ya_avisados:
            continue
        cerca_por_orden = indice <= 2  # quedan 2 paradas antes de la suya (parada 0 = actual, 1 = prox, 2 = 2 antes)
        cerca_por_distancia = False
        if ubicacion is not None and pedido.longitud is not None:
            cerca_por_distancia = calcular_distancia(
                ubicacion.latitud, ubicacion.longitud, pedido.latitud, pedido.longitud,
            ) <= UMBRAL_CERCA_KM
        if cerca_por_orden or cerca_por_distancia:
            # registrar es best-effort y no lanza: un pedido con error no corta a los demas.
            creados += operador.registrar(db, EVENTO, {"pedido": pedido, "ocurrencia": ocurrencia})
    return creados
