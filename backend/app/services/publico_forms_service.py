from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories import reclamo_repository as repo
from app.services import correo_service
from app.schemas.portal import ContactoIn, ReclamoIn


def registrar_contacto(db: Session, datos: ContactoIn) -> dict:
    """Guarda un lead de contacto + avisa a ventas por correo. Recibe ContactoIn.
    Honeypot: si 'hp' trae texto, se ignora (probable bot) devolviendo ok."""
    if datos.hp:
        return {"ok": True}
    repo.crear_contacto(db, {
        "nombre": datos.nombre, "empresa": datos.empresa, "email": datos.email,
        "telefono": datos.telefono, "volumen_estimado": datos.volumen, "mensaje": datos.mensaje,
    })
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
    bien = datos.bien
    reclamo = repo.crear_reclamo(db, {
        "tipo": datos.tipo,
        "consumidor_nombre": datos.consumidor.nombre,
        "consumidor_dni": datos.consumidor.dni,
        "consumidor_domicilio": datos.consumidor.domicilio,
        "consumidor_email": datos.consumidor.email,
        "consumidor_telefono": datos.consumidor.telefono,
        "es_menor": datos.consumidor.esMenor,
        "bien_tipo": bien.tipo if bien else None,
        "bien_descripcion": bien.descripcion if bien else None,
        "monto_reclamado": bien.monto if bien else None,
        "detalle": datos.detalle,
        "pedido_codigo": datos.pedido,
    })
    # correo a la empresa
    correo_service.enviar_simple(
        settings.correo_reclamos, f"Nuevo {datos.tipo.lower()} {reclamo.codigo}",
        f"Codigo: {reclamo.codigo}\nTipo: {datos.tipo}\nConsumidor: {datos.consumidor.nombre}\n"
        f"DNI: {datos.consumidor.dni}\nDetalle: {datos.detalle}",
    )
    # acuse al consumidor
    if datos.consumidor.email:
        correo_service.enviar_simple(
            datos.consumidor.email, f"Registramos su {datos.tipo.lower()} — {reclamo.codigo}",
            f"Hemos registrado su {datos.tipo.lower()} con codigo {reclamo.codigo}. "
            "Le responderemos en el plazo de ley (15 dias habiles).",
        )
    return {"codigo": reclamo.codigo}
