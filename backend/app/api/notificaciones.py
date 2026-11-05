"""Endpoints del Centro de Notificaciones:
- Historial interno de notificaciones admin (campana).
- Directorio de mecánicos (CRUD, verificación por código y asignación del auxilio).
- Bitácora de envíos externos (notificaciones_envios) y plantillas editables.
- Enlaces de Telegram para conductores.
- Webhooks de mensajería (Telegram y WhatsApp): solo se aceptan si los firma el proveedor.
La lógica vive en services/notificaciones_automaticas (administracion, webhooks).
"""
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.api.deps import get_current_admin
from app.db.database import get_db
from app.schemas.notificacion import NotificacionesResponse
from app.schemas.notificacion_mecanico import (
    AsignarMecanico, MecanicoCreate, MecanicoUpdate, MecanicoVerificarOtp, PlantillaUpdate,
)
from app.services import notificaciones_service
from app.services.notificaciones_automaticas import administracion, webhooks

router = APIRouter()


# ---------------------------------------------------------
# 1. Alertas internas del panel (Campana)
# ---------------------------------------------------------

@router.get("", response_model=NotificacionesResponse, dependencies=[Depends(get_current_admin)])
def listar_notificaciones(limite: int = 50, db: Session = Depends(get_db)):
    """Lista notificaciones internas del admin con contador de no vistas. Recibe el limite."""
    return notificaciones_service.listar(db, limite=max(1, min(limite, 500)))


@router.post("/marcar-vistas", dependencies=[Depends(get_current_admin)])
def marcar_vistas(db: Session = Depends(get_db)):
    """Marca todas las notificaciones internas como vistas. Sin input."""
    return {"marcadas": notificaciones_service.marcar_vistas(db)}


# ---------------------------------------------------------
# 2. Bitácora de envíos externos
# ---------------------------------------------------------

@router.get("/envios", dependencies=[Depends(get_current_admin)])
def listar_envios(
    estado: Optional[str] = None,
    canal: Optional[str] = None,
    evento: Optional[str] = None,
    limite: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Bitácora de mensajes enviados, pendientes o fallidos. Recibe filtros y paginación."""
    return administracion.listar_envios(db, estado, canal, evento, limite, offset)


@router.post("/envios/{envio_id}/reintentar", dependencies=[Depends(get_current_admin)])
def reintentar_envio(envio_id: int, db: Session = Depends(get_db)):
    """Vuelve a poner en cola un envío fallido. Recibe el id."""
    return administracion.reintentar_envio(db, envio_id)


# ---------------------------------------------------------
# 3. Directorio de mecánicos y auxilio
# ---------------------------------------------------------

@router.get("/mecanicos", dependencies=[Depends(get_current_admin)])
def listar_mecanicos(db: Session = Depends(get_db)):
    """Lista los mecánicos y proveedores de auxilio. Sin input."""
    return administracion.listar_mecanicos(db)


@router.post("/mecanicos", dependencies=[Depends(get_current_admin)])
def crear_mecanico(datos: MecanicoCreate, db: Session = Depends(get_db)):
    """Da de alta un mecánico (queda sin verificar). Recibe sus datos."""
    return administracion.crear_mecanico(db, datos)


@router.put("/mecanicos/{mecanico_id}", dependencies=[Depends(get_current_admin)])
def actualizar_mecanico(mecanico_id: int, datos: MecanicoUpdate, db: Session = Depends(get_db)):
    """Edita un mecánico. Recibe el id y los datos."""
    return administracion.actualizar_mecanico(db, mecanico_id, datos)


@router.delete("/mecanicos/{mecanico_id}", dependencies=[Depends(get_current_admin)])
def eliminar_mecanico(mecanico_id: int, db: Session = Depends(get_db)):
    """Quita un mecánico del directorio. Recibe el id."""
    return administracion.eliminar_mecanico(db, mecanico_id)


@router.post("/mecanicos/{mecanico_id}/enviar-codigo", dependencies=[Depends(get_current_admin)])
def enviar_codigo_verificacion_mecanico(mecanico_id: int, db: Session = Depends(get_db)):
    """Envía un código de 6 dígitos al mecánico para verificar su número. Recibe el id."""
    return administracion.enviar_codigo(db, mecanico_id)


@router.post("/mecanicos/{mecanico_id}/verificar", dependencies=[Depends(get_current_admin)])
def verificar_mecanico(mecanico_id: int, datos: MecanicoVerificarOtp, db: Session = Depends(get_db)):
    """Verifica el número del mecánico con su código. Recibe el id y el código."""
    return administracion.verificar_mecanico(db, mecanico_id, datos.codigo)


@router.get("/mecanicos/propuesta/{incidencia_id}", dependencies=[Depends(get_current_admin)])
def proponer_mecanico_cercano(incidencia_id: int, tipo: Optional[str] = None, db: Session = Depends(get_db)):
    """Propone al mecánico verificado más cercano (o al siguiente). Recibe la incidencia y el tipo."""
    return administracion.proponer_mecanico(db, incidencia_id, tipo)


@router.post("/mecanicos/asignar/{incidencia_id}", dependencies=[Depends(get_current_admin)])
def asignar_mecanico(incidencia_id: int, datos: AsignarMecanico, db: Session = Depends(get_db)):
    """Envía el auxilio al mecánico que confirmó el administrador. Recibe la incidencia y el mecánico."""
    return administracion.asignar_mecanico(db, incidencia_id, datos.mecanico_id)


# ---------------------------------------------------------
# 4. Telegram de los conductores
# ---------------------------------------------------------

@router.get("/telegram/conductores", dependencies=[Depends(get_current_admin)])
def conductores_con_telegram(db: Session = Depends(get_db)):
    """Conductores que ya vincularon su Telegram. Sin input."""
    return administracion.conductores_vinculados(db)


@router.get("/telegram/conductores/{conductor_id}/enlace", dependencies=[Depends(get_current_admin)])
def enlace_telegram_conductor(conductor_id: int, db: Session = Depends(get_db)):
    """Enlace firmado para que un conductor vincule su Telegram. Recibe el id del conductor."""
    return administracion.enlace_conductor(db, conductor_id)


# ---------------------------------------------------------
# 5. Plantillas
# ---------------------------------------------------------

@router.get("/plantillas", dependencies=[Depends(get_current_admin)])
def listar_plantillas(db: Session = Depends(get_db)):
    """Plantillas de los avisos (crea las de fábrica que falten). Sin input."""
    return administracion.listar_plantillas(db)


@router.put("/plantillas/{plantilla_id}", dependencies=[Depends(get_current_admin)])
def actualizar_plantilla(plantilla_id: int, datos: PlantillaUpdate, db: Session = Depends(get_db)):
    """Cambia el texto o enciende/apaga un aviso. Recibe el id y los datos."""
    return administracion.actualizar_plantilla(db, plantilla_id, datos)


# ---------------------------------------------------------
# 6. Webhooks (solo los acepta si los firma el proveedor)
# ---------------------------------------------------------

@router.post("/webhook/telegram")
async def webhook_telegram(request: Request, db: Session = Depends(get_db)):
    """Recibe mensajes y botones de Telegram (/start, STOP, AYUDA, VOY, NO PUEDO). Recibe el JSON."""
    if not webhooks.verificar_telegram(request.headers.get("X-Telegram-Bot-Api-Secret-Token")):
        raise HTTPException(status_code=403, detail="Webhook no autorizado")
    try:
        payload = await request.json()
    except ValueError:
        raise HTTPException(status_code=400, detail="Cuerpo inválido")
    return await run_in_threadpool(webhooks.procesar_telegram, db, payload)


@router.get("/webhook/whatsapp")
def verificar_webhook_whatsapp(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_token: Optional[str] = Query(None, alias="hub.verify_token"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
):
    """Handshake de Meta al registrar el webhook. Recibe los parámetros hub.*."""
    if not webhooks.verificar_handshake(hub_mode, hub_token):
        raise HTTPException(status_code=403, detail="Token de verificación incorrecto")
    return PlainTextResponse(content=hub_challenge or "")


@router.post("/webhook/whatsapp")
async def recibir_webhook_whatsapp(request: Request, db: Session = Depends(get_db)):
    """Recibe mensajes de WhatsApp Cloud API (STOP, AYUDA, VOY, NO PUEDO). Recibe el JSON firmado."""
    cuerpo = await request.body()
    if not webhooks.verificar_firma_whatsapp(cuerpo, request.headers.get("X-Hub-Signature-256")):
        raise HTTPException(status_code=403, detail="Firma inválida")
    try:
        payload = json.loads(cuerpo)
    except ValueError:
        raise HTTPException(status_code=400, detail="Cuerpo inválido")
    return await run_in_threadpool(webhooks.procesar_whatsapp, db, payload)
