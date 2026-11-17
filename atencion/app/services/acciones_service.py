# Ejecuta lo que el visitante confirma con un clic en la tarjeta (OWASP LLM06: el modelo solo
# propone). Aqui no participa el modelo: se usan los datos reales guardados en memoria al proponer
# y la API publica del portal, con el token de portal del pedido verificado y la IP del visitante.
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.registro import log
from app.herramientas.cliente_portal import ClientePortal, ErrorPortal, Rechazado, SesionVencida
from app.models.conversacion import Conversacion
from app.repositories import conversacion_repository, gestion_repository
from app.services.sesion import EstadoConversacion

TEXTOS = {
    "es": {
        "reprogramar_ok": "Listo: se registró tu solicitud para reprogramar el pedido {codigo} en la franja «{franja}». "
                          "El equipo de SAVA la revisará y la verás en el portal.",
        "contacto_ok": "¡Gracias! Enviamos tus datos al equipo comercial de SAVA; te responderán con una propuesta en 24 horas.",
        "cancelada": "Listo, no se hizo ningún cambio.",
        "vencida": "Esa propuesta venció. Pídemelo de nuevo y te muestro una nueva.",
        "verificar": "La verificación del pedido venció. Vuelve a verificarlo y te muestro la propuesta otra vez.",
        "limite": "Esta conversación ya no puede registrar más solicitudes. Escríbenos al WhatsApp +51 922 507 593.",
        "error": "No se pudo completar: {motivo}",
        "caido": "El sistema no responde en este momento. Inténtalo en unos minutos o escríbenos al WhatsApp +51 922 507 593.",
    },
    "en": {
        "reprogramar_ok": "Done: your request to reschedule order {codigo} for «{franja}» was registered. "
                          "The SAVA team will review it and you will see it in the portal.",
        "contacto_ok": "Thank you! We sent your details to SAVA's sales team; they will reply with a proposal within 24 hours.",
        "cancelada": "Okay, nothing was changed.",
        "vencida": "That proposal expired. Ask me again and I'll show you a new one.",
        "verificar": "The order verification expired. Verify it again and I'll show you the proposal again.",
        "limite": "This conversation can't register more requests. Write to us on WhatsApp +51 922 507 593.",
        "error": "It could not be completed: {motivo}",
        "caido": "The system is not responding right now. Try again in a few minutes or write to us on WhatsApp +51 922 507 593.",
    },
}


class AccionNoValida(Exception):
    """La accion no existe, no es de esta conversacion o ya se resolvio."""


def _cerrar(db: Session, conversacion: Conversacion, accion, estado: str, texto: str, resultado: str | None = None) -> dict:
    """Cierra la accion, deja el mensaje en la conversacion y arma la respuesta. Recibe db, conversacion,
    accion, estado, texto para el visitante y resultado para la auditoria."""
    gestion_repository.resolver_accion(db, accion, estado, resultado or estado.lower())
    conversacion_repository.agregar_mensaje(db, conversacion, "asistente", texto, idioma=conversacion.idioma, modo="accion")
    return {"id": accion.id, "estado": estado, "mensaje": texto}


def _accion_de(db: Session, conversacion: Conversacion, ident: str):
    """Accion pendiente de ESTA conversacion, o error. Recibe db, conversacion e id."""
    accion = gestion_repository.obtener_accion(db, ident)
    if accion is None or accion.conversacion_id != conversacion.id or accion.estado != "PENDIENTE":
        raise AccionNoValida("La acción no existe o ya se resolvió")
    return accion


def cancelar(db: Session, conversacion: Conversacion, estado: EstadoConversacion, ident: str) -> dict:
    """Cancela una propuesta pendiente. Recibe db, conversacion, estado en memoria e id."""
    accion = _accion_de(db, conversacion, ident)
    estado.propuestas.pop(ident, None)
    return _cerrar(db, conversacion, accion, "CANCELADA", TEXTOS[conversacion.idioma]["cancelada"])


async def confirmar(db: Session, conversacion: Conversacion, estado: EstadoConversacion, ident: str,
                    portal: ClientePortal) -> dict:
    """Ejecuta una propuesta que el visitante confirmo. Recibe db, conversacion, estado en memoria, id y portal."""
    t = TEXTOS.get(conversacion.idioma, TEXTOS["es"])
    accion = _accion_de(db, conversacion, ident)
    propuesta = estado.propuesta(ident)
    if propuesta is None:
        return _cerrar(db, conversacion, accion, "VENCIDA", t["vencida"])
    if estado.acciones >= settings.ATENCION_ACCIONES_POR_CONVERSACION:
        estado.propuestas.pop(ident, None)
        return _cerrar(db, conversacion, accion, "ERROR", t["limite"], "límite de acciones")
    datos = propuesta.datos
    try:
        if propuesta.tipo == "reprogramar":
            token = estado.token(datos["codigo"])
            if not token:
                raise SesionVencida("sin token")
            await portal.reprogramar(datos["codigo"], datos["franja"], token)
            texto = t["reprogramar_ok"].format(**datos)
        else:
            await portal.contacto(datos)
            texto = t["contacto_ok"]
    except SesionVencida:
        estado.propuestas.pop(ident, None)
        estado.olvidar_token(datos.get("codigo", ""))
        return _cerrar(db, conversacion, accion, "ERROR", t["verificar"], "verificación vencida")
    except Rechazado as exc:
        estado.propuestas.pop(ident, None)
        return _cerrar(db, conversacion, accion, "ERROR", t["error"].format(motivo=str(exc)[:200]), str(exc))
    except ErrorPortal as exc:
        # El portal no respondio: la propuesta sigue pendiente para reintentar el clic.
        log.warning("No se pudo ejecutar la acción %s: %s", ident[:8], exc)
        return {"id": ident, "estado": "PENDIENTE", "mensaje": t["caido"]}
    estado.propuestas.pop(ident, None)
    estado.acciones += 1
    log.info("Acción %s confirmada por el visitante (conversación %s)", propuesta.tipo, conversacion.id[:8])
    return _cerrar(db, conversacion, accion, "CONFIRMADA", texto)
