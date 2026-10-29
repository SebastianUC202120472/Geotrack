# Libro de Reclamaciones: constancia, plazo legal y respuesta al consumidor (C40-02, C41-01..03),
# y contactos comerciales del landing (C39-01).
import io
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core import fechas
from app.core.config import settings
from app.core.plazos import PLAZO_RECLAMO_DIAS_HABILES, sumar_dias_habiles, dias_habiles_entre
from app.repositories import reclamo_repository as repo
from app.services import correo_service

# Dias habiles restantes desde los que el reclamo se marca "por vencer".
AVISO_POR_VENCER = 3


def datos_proveedor() -> dict:
    """Razon social, RUC y direccion de SAVA que muestra el Libro (C40-02)."""
    return {
        "razonSocial": settings.EMPRESA_RAZON_SOCIAL,
        "ruc": settings.EMPRESA_RUC.strip() or None,
        "direccion": settings.EMPRESA_DIRECCION,
    }


def vence_el(reclamo):
    """Fecha local en que vence el plazo legal de respuesta (15 dias habiles). Recibe el reclamo."""
    registrado = fechas.fecha_local_de(reclamo.creado_en or datetime.utcnow())
    return sumar_dias_habiles(registrado, PLAZO_RECLAMO_DIAS_HABILES)


def plazo(reclamo, hoy=None) -> dict:
    """Estado del plazo legal: fecha limite, dias habiles restantes y alerta. Recibe el reclamo y hoy (opcional)."""
    limite = vence_el(reclamo)
    if reclamo.respondido_en:
        return {"venceEl": limite.isoformat(), "diasRestantes": None, "estado": "RESPONDIDO",
                "aTiempo": fechas.fecha_local_de(reclamo.respondido_en) <= limite}
    restantes = dias_habiles_entre(hoy or fechas.hoy_local(), limite)
    estado = "VENCIDO" if restantes < 0 else "POR_VENCER" if restantes <= AVISO_POR_VENCER else "EN_PLAZO"
    return {"venceEl": limite.isoformat(), "diasRestantes": restantes, "estado": estado, "aTiempo": None}


def constancia(reclamo) -> dict:
    """Copia de la hoja de reclamacion para mostrar e imprimir al registrarla (C40-02). Recibe el reclamo."""
    return {
        "codigo": reclamo.codigo,
        "fecha": reclamo.creado_en.isoformat() if reclamo.creado_en else None,
        "proveedor": datos_proveedor(),
        "tipo": reclamo.tipo,
        "consumidor": {
            "nombre": reclamo.consumidor_nombre, "documento": reclamo.consumidor_dni,
            "domicilio": reclamo.consumidor_domicilio, "telefono": reclamo.consumidor_telefono,
            "email": reclamo.consumidor_email, "esMenor": bool(reclamo.es_menor),
            "apoderadoNombre": reclamo.apoderado_nombre, "apoderadoDni": reclamo.apoderado_dni,
        },
        "bien": {"tipo": reclamo.bien_tipo, "descripcion": reclamo.bien_descripcion, "monto": reclamo.monto_reclamado},
        "detalle": reclamo.detalle,
        "pedidoConsumidor": reclamo.pedido_consumidor,
        "pedido": reclamo.pedido_codigo,
        "venceEl": vence_el(reclamo).isoformat(),
    }


def texto_constancia(reclamo) -> str:
    """Constancia en texto plano para el correo (copia completa del reclamo). Recibe el reclamo."""
    c = constancia(reclamo)
    p, con, bien = c["proveedor"], c["consumidor"], c["bien"]
    lineas = [
        f"HOJA DE RECLAMACIÓN {c['codigo']}",
        f"Proveedor: {p['razonSocial']}" + (f" · RUC {p['ruc']}" if p["ruc"] else ""),
        f"Dirección: {p['direccion']}",
        f"Fecha: {fechas.fecha_local_de(reclamo.creado_en).strftime('%d/%m/%Y')}",
        "",
        f"Tipo: {c['tipo']}",
        f"Consumidor: {con['nombre']} · Doc. {con['documento']}",
        f"Domicilio: {con['domicilio']}",
        f"Teléfono: {con['telefono']} · Correo: {con['email']}",
    ]
    if con["esMenor"]:
        lineas.append(f"Padre o madre: {con['apoderadoNombre']} · Doc. {con['apoderadoDni']}")
    lineas += [
        f"Bien contratado: {bien['tipo']} — {bien['descripcion']}",
        f"Monto reclamado: S/ {bien['monto']:.2f}" if bien["monto"] is not None else "Monto reclamado: —",
        f"Pedido SAVA: {c['pedido'] or '—'}",
        "",
        f"Detalle: {c['detalle']}",
        f"Pedido del consumidor: {c['pedidoConsumidor']}",
        "",
        f"Le responderemos a más tardar el {vence_el(reclamo).strftime('%d/%m/%Y')} "
        f"({PLAZO_RECLAMO_DIAS_HABILES} días hábiles, Ley N.º 29571).",
    ]
    return "\n".join(lineas)


def a_dict(reclamo, hoy=None) -> dict:
    """Reclamo completo para el panel, con su plazo legal (C41-01, C41-03). Recibe el reclamo."""
    return {
        "id": reclamo.id, "codigo": reclamo.codigo, "tipo": reclamo.tipo,
        "consumidor": reclamo.consumidor_nombre, "dni": reclamo.consumidor_dni,
        "domicilio": reclamo.consumidor_domicilio, "telefono": reclamo.consumidor_telefono,
        "email": reclamo.consumidor_email, "esMenor": bool(reclamo.es_menor),
        "apoderadoNombre": reclamo.apoderado_nombre, "apoderadoDni": reclamo.apoderado_dni,
        "bienTipo": reclamo.bien_tipo, "bienDescripcion": reclamo.bien_descripcion,
        "monto": reclamo.monto_reclamado, "detalle": reclamo.detalle,
        "pedidoConsumidor": reclamo.pedido_consumidor, "pedido": reclamo.pedido_codigo,
        "respuesta": reclamo.respuesta,
        "respondidoEn": reclamo.respondido_en.isoformat() if reclamo.respondido_en else None,
        "creado_en": reclamo.creado_en.isoformat() if reclamo.creado_en else None,
        "plazo": plazo(reclamo, hoy),
    }


def listar(db: Session) -> list:
    """Reclamos con su plazo, los mas recientes primero. Recibe la sesion."""
    hoy = fechas.hoy_local()
    return [a_dict(r, hoy) for r in repo.listar_reclamos(db)]


def responder(db: Session, reclamo_id: int, respuesta: str, admin_id: int) -> dict:
    """Registra la respuesta al consumidor y su fecha (C41-02) y se la envia por correo si esta
    configurado. El reclamo en si no se edita. Recibe id, respuesta y el admin."""
    reclamo = repo.obtener_reclamo(db, reclamo_id)
    if not reclamo:
        raise HTTPException(status_code=404, detail="Reclamo no encontrado")
    if reclamo.respondido_en:
        raise HTTPException(status_code=409, detail="Este reclamo ya fue respondido.")
    reclamo.respuesta = respuesta
    reclamo.respondido_en = datetime.utcnow()
    reclamo.respondido_por = admin_id
    repo.guardar(db)
    enviado = correo_service.enviar_simple(
        reclamo.consumidor_email, f"Respuesta a su {reclamo.tipo.lower()} {reclamo.codigo}",
        f"{respuesta}\n\n{settings.firma}")
    return {**a_dict(reclamo), "correoEnviado": bool(enviado)}


def contactos(db: Session) -> list:
    """Contactos comerciales del landing, los mas recientes primero (C39-01). Recibe la sesion."""
    return [
        {"id": c.id, "nombre": c.nombre, "empresa": c.empresa, "email": c.email, "telefono": c.telefono,
         "volumen": c.volumen_estimado, "mensaje": c.mensaje,
         "creado_en": c.creado_en.isoformat() if c.creado_en else None}
        for c in repo.listar_contactos(db)
    ]


def excel_contactos(db: Session) -> bytes:
    """Exporta los contactos comerciales a Excel (C39-01). Recibe la sesion. Devuelve los bytes del .xlsx."""
    from openpyxl import Workbook
    from openpyxl.styles import Font

    filas = repo.listar_contactos(db)
    wb = Workbook()
    hoja = wb.active
    hoja.title = "Contactos"
    hoja.append(["Fecha", "Nombre", "Empresa", "Correo", "Teléfono", "Pedidos al día", "Mensaje"])
    for celda in hoja[1]:
        celda.font = Font(bold=True)
    for c in filas:
        fecha = fechas.fecha_local_de(c.creado_en).strftime("%d/%m/%Y") if c.creado_en else ""
        hoja.append([fecha, c.nombre, c.empresa or "", c.email, c.telefono or "", c.volumen_estimado, c.mensaje or ""])
    for letra, ancho in zip("ABCDEFG", (12, 26, 26, 30, 16, 14, 60)):
        hoja.column_dimensions[letra].width = ancho
    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()
