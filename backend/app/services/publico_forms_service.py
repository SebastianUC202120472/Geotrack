from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories import reclamo_repository as repo
from app.services import correo_service, notificaciones_service, reclamo_service
from app.schemas.portal import ContactoIn, ReclamoIn


def registrar_contacto(db: Session, datos: ContactoIn) -> dict:
    """Guarda un lead de contacto + avisa a ventas por correo. Recibe ContactoIn.
    Honeypot: si 'hp' trae texto, se ignora (probable bot) devolviendo ok."""
    if datos.hp:
        return {"ok": True}
    lead = repo.crear_contacto(db, {
        "nombre": datos.nombre, "empresa": datos.empresa, "email": datos.email,
        "telefono": datos.telefono, "volumen_estimado": datos.volumen, "mensaje": datos.mensaje,
    })
    # Aviso en la campana del panel: con el correo apagado es la unica forma de enterarse (C37-01).
    notificaciones_service.registrar(
        db, "contactos", "Nuevo contacto comercial",
        f"{datos.nombre}{f' · {datos.empresa}' if datos.empresa else ''}", "/contactos", lead.id)
    correo_service.enviar_simple(
        settings.correo_ventas, "Nuevo lead de contacto — sava.pe",
        f"Nombre: {datos.nombre}\nEmpresa: {datos.empresa}\nEmail: {datos.email}\n"
        f"Telefono: {datos.telefono}\nVolumen: {datos.volumen}\nMensaje: {datos.mensaje}",
    )
    return {"ok": True}


def registrar_reclamo(db: Session, datos: ReclamoIn) -> dict:
    """Guarda un reclamo (Ley 29571), genera codigo LR y envia correos. Recibe ReclamoIn. Devuelve {codigo}."""
    if datos.hp:
        return {"codigo": "LR-0000-0000"}
    if datos.tipo not in ("RECLAMO", "QUEJA"):
        raise HTTPException(status_code=400, detail="Tipo invalido (RECLAMO|QUEJA)")
    bien, consumidor = datos.bien, datos.consumidor
    reclamo = repo.crear_reclamo(db, {
        "tipo": datos.tipo,
        "consumidor_nombre": consumidor.nombre,
        "consumidor_dni": consumidor.dni,
        "consumidor_domicilio": consumidor.domicilio,
        "consumidor_email": str(consumidor.email),
        "consumidor_telefono": consumidor.telefono,
        "es_menor": consumidor.esMenor,
        "apoderado_nombre": consumidor.apoderadoNombre,
        "apoderado_dni": consumidor.apoderadoDni,
        "bien_tipo": bien.tipo,
        "bien_descripcion": bien.descripcion,
        "monto_reclamado": bien.monto,
        "detalle": datos.detalle,
        "pedido_consumidor": datos.pedidoConsumidor,
        "pedido_codigo": (datos.pedido or "").strip().upper() or None,
    })
    copia = reclamo_service.texto_constancia(reclamo)
    # Aviso en la campana: el plazo legal corre desde hoy (C37-01).
    notificaciones_service.registrar(
        db, "reclamos", f"Nuevo {datos.tipo.lower()} {reclamo.codigo}",
        f"{consumidor.nombre} · responder antes del {reclamo_service.vence_el(reclamo).strftime('%d/%m/%Y')}",
        f"/reclamos?codigo={reclamo.codigo}", reclamo.id)
    correo_service.enviar_simple(settings.correo_reclamos, f"Nuevo {datos.tipo.lower()} {reclamo.codigo}", copia)
    # Constancia al consumidor con copia completa de su hoja de reclamacion (C40-02).
    correo_service.enviar_simple(
        str(consumidor.email), f"Constancia de su {datos.tipo.lower()} — {reclamo.codigo}", copia)
    return {"codigo": reclamo.codigo, "constancia": reclamo_service.constancia(reclamo)}
