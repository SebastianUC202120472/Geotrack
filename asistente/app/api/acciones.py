# Confirmar o cancelar una accion propuesta por el asistente. Es el UNICO camino que escribe en
# el nucleo y solo se llega con el clic del usuario en la tarjeta (nunca desde el chat ni el modelo):
#   - misma persona y misma sesion que recibio la propuesta, con un rol que puede hacer la accion;
#   - propuesta PENDIENTE y vigente (5 minutos); el paso a EN_CURSO es atomico: un doble clic
#     ejecuta una sola vez;
#   - la escritura va con el token del usuario, asi que el nucleo vuelve a validar rol y estado;
#   - cada paso queda en la auditoria de acciones.
from fastapi import APIRouter, Depends, Header, HTTPException, Path, Request, status
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.api.deps import obtener_usuario
from app.core.config import settings
from app.core.limites import limitador
from app.core.registro import log
from app.db.database import get_db
from app.herramientas import acciones
from app.herramientas.cliente_core import ClienteCore, ErrorCore, NoEncontrado, Rechazado, SesionInvalida, SinPermiso
from app.models import propuesta_accion as M
from app.repositories import accion_repository as repo
from app.schemas.chat import ResultadoAccion

router = APIRouter()
_ID = Path(pattern=r"^[a-f0-9]{32}$")
# Cabecera propia del widget: un formulario de otro sitio no puede enviarla sin pasar por CORS.
CABECERA = "X-Asistente-Confirmacion"
_MENSAJES_ESTADO = {
    M.EN_CURSO: "Esta acción ya se está ejecutando.",
    M.EJECUTADA: "Esta acción ya se ejecutó.",
    M.ERROR: "Esta acción ya se intentó y falló.",
    M.CANCELADA: "Esta acción fue cancelada.",
    M.VENCIDA: "La propuesta venció. Pídesela de nuevo al asistente.",
    M.INVALIDADA: "La propuesta ya no es válida (cambiaste de conversación). Pídesela de nuevo al asistente.",
}


def _exigir_activas() -> None:
    """Corta si las acciones estan apagadas. Sin input."""
    if not acciones.activas():
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Las acciones del asistente están desactivadas")


def _exigir_cabecera(valor: str | None) -> None:
    """Exige la cabecera propia del widget. Recibe su valor."""
    if valor != "si":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Falta la confirmación del panel")


def _propuesta_del_usuario(db: Session, propuesta_id: str, usuario: dict, operacion: str) -> M.PropuestaAccion:
    """Carga la propuesta y verifica dueño, sesion y rol; audita el rechazo. Recibe db, id, usuario y operacion."""
    propuesta = repo.obtener(db, propuesta_id)
    if propuesta is None or propuesta.usuario_id != usuario["id"]:
        repo.auditar(db, usuario, "rechazada", propuesta if propuesta else None,
                     detalle=f"{operacion}: propuesta {'ajena' if propuesta else 'inexistente'} ({propuesta_id})")
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Propuesta no encontrada")
    accion = acciones.ACCIONES.get(propuesta.accion)
    if accion is None or usuario["rol"] not in accion.roles or usuario["rol"] != propuesta.rol:
        repo.auditar(db, usuario, "rechazada", propuesta, detalle=f"{operacion}: rol {usuario['rol']} sin permiso")
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Tu rol no puede hacer esta acción")
    if propuesta.sesion != acciones.huella_sesion(usuario["token"]):
        repo.auditar(db, usuario, "rechazada", propuesta, detalle=f"{operacion}: otra sesión")
        raise HTTPException(status.HTTP_409_CONFLICT, "La propuesta es de otra sesión. Pídesela de nuevo al asistente.")
    return propuesta


def _no_pendiente(db: Session, propuesta: M.PropuestaAccion, usuario: dict, operacion: str) -> HTTPException:
    """Error para una propuesta que ya no esta PENDIENTE (doble clic, vencida, cancelada). Recibe db, propuesta, usuario y operacion."""
    db.refresh(propuesta)
    if propuesta.estado != M.VENCIDA:
        repo.auditar(db, usuario, "rechazada", propuesta, detalle=f"{operacion}: estado {propuesta.estado}")
    codigo = status.HTTP_410_GONE if propuesta.estado in (M.VENCIDA, M.INVALIDADA) else status.HTTP_409_CONFLICT
    return HTTPException(codigo, _MENSAJES_ESTADO.get(propuesta.estado, "La propuesta ya no está pendiente."))


def _tomar(db: Session, propuesta_id: str, usuario: dict) -> M.PropuestaAccion:
    """Verifica y pasa la propuesta a EN_CURSO (una sola vez) y audita la confirmacion. Recibe db, id y usuario."""
    propuesta = _propuesta_del_usuario(db, propuesta_id, usuario, "confirmar")
    repo.vencer_si_corresponde(db, propuesta, usuario)
    if not repo.tomar_para_ejecutar(db, propuesta.id):
        raise _no_pendiente(db, propuesta, usuario, "confirmar")
    repo.auditar(db, usuario, "confirmada", propuesta)
    return propuesta


def _cerrar(db: Session, propuesta: M.PropuestaAccion, usuario: dict, ok: bool, mensaje: str) -> None:
    """Guarda el resultado y lo audita con el usuario que confirmo. Recibe db, propuesta, usuario, resultado y mensaje."""
    repo.terminar(db, propuesta.id, ok, mensaje)
    repo.auditar(db, usuario, "ejecutada" if ok else "error", propuesta, detalle=mensaje)


@router.post("/{propuesta_id}/confirmar", response_model=ResultadoAccion)
async def confirmar(
    request: Request,
    propuesta_id: str = _ID,
    confirmacion: str | None = Header(default=None, alias=CABECERA),
    db: Session = Depends(get_db),
    usuario: dict = Depends(obtener_usuario),
):
    """Ejecuta la accion propuesta tras el clic del usuario. Recibe el id de la propuesta."""
    _exigir_activas()
    _exigir_cabecera(confirmacion)
    if not limitador.permitir(f"accion:{usuario['id']}", settings.ASISTENTE_ACCIONES_POR_MINUTO, 60):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Demasiadas confirmaciones seguidas: espera un minuto.")
    propuesta = await run_in_threadpool(_tomar, db, propuesta_id, usuario)

    core = ClienteCore(usuario["token"], getattr(request.app.state, "http_core", None))
    try:
        ok, mensaje = await acciones.ejecutar(propuesta.accion, propuesta.objetivo, core)
    except (Rechazado, NoEncontrado) as exc:
        ok, mensaje = False, str(exc)
    except SesionInvalida:
        ok, mensaje = False, "Tu sesión expiró. Vuelve a iniciar sesión y pide la acción otra vez."
    except SinPermiso:
        ok, mensaje = False, "El sistema no permite esta acción a tu rol."
    except ErrorCore as exc:
        # Sin respuesta clara del nucleo no se sabe si se aplico: no se reintenta.
        log.warning("Accion %s fallo: %s", propuesta.accion, exc)
        ok, mensaje = False, "No se pudo confirmar el resultado con el sistema. Revisa el pedido en el panel antes de reintentar."
    await run_in_threadpool(_cerrar, db, propuesta, usuario, ok, mensaje)
    return ResultadoAccion(id=propuesta.id, estado=M.EJECUTADA if ok else M.ERROR, mensaje=mensaje)


def _cancelar(db: Session, propuesta_id: str, usuario: dict) -> M.PropuestaAccion:
    """Verifica y cancela la propuesta; audita la cancelacion. Recibe db, id y usuario."""
    propuesta = _propuesta_del_usuario(db, propuesta_id, usuario, "cancelar")
    repo.vencer_si_corresponde(db, propuesta, usuario)
    if not repo.cancelar(db, propuesta.id):
        raise _no_pendiente(db, propuesta, usuario, "cancelar")
    repo.auditar(db, usuario, "cancelada", propuesta)
    return propuesta


@router.post("/{propuesta_id}/cancelar", response_model=ResultadoAccion)
async def cancelar(
    propuesta_id: str = _ID,
    confirmacion: str | None = Header(default=None, alias=CABECERA),
    db: Session = Depends(get_db),
    usuario: dict = Depends(obtener_usuario),
):
    """Descarta la accion propuesta sin hacer cambios. Recibe el id de la propuesta."""
    _exigir_activas()
    _exigir_cabecera(confirmacion)
    propuesta = await run_in_threadpool(_cancelar, db, propuesta_id, usuario)
    return ResultadoAccion(id=propuesta.id, estado=M.CANCELADA, mensaje="Cancelada: no se hizo ningún cambio.")
