import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.config import settings
from app.core.rate_limit import limite_publico
from app.core import portal_token
from app.core.security import verify_password
from app.services import portal_service, verificacion_portal_service as verif
from app.services import correo_service, enmascarado, publico_forms_service
from app.repositories import portal_repository as repo
from app.schemas.portal import VerificarDni, Reprogramar, EmpresaLogin, EmpresaVerificar, ContactoIn, ReclamoIn

router = APIRouter()


@router.get("/estadisticas", dependencies=[Depends(limite_publico(30, 60))])
def estadisticas(db: Session = Depends(get_db)):
    """Estadisticas agregadas para el landing (publico, sin datos personales)."""
    return portal_service.estadisticas_publicas(db)


@router.get("/demo", dependencies=[Depends(limite_publico(30, 60))])
def ayuda_demo(db: Session = Depends(get_db)):
    """Credenciales y codigos de ejemplo de la demostracion, para mostrarlos en el portal.
    Sin input. Devuelve {"activo": false} si el modo demostracion esta apagado."""
    return portal_service.ayuda_demo(db, settings.PORTAL_OTP_DEMO)


@router.post("/pedidos/{codigo}/buscar", dependencies=[Depends(limite_publico(30, 60))])
def buscar_pedido(codigo: str, db: Session = Depends(get_db)):
    """Resumen enmascarado de un pedido (pre-verificacion). Recibe el codigo en la ruta."""
    return portal_service.buscar_resumen(db, codigo.upper())


@router.post("/pedidos/{codigo}/verificar", dependencies=[Depends(limite_publico(10, 60))])
def verificar_pedido(codigo: str, datos: VerificarDni, db: Session = Depends(get_db)):
    """Verifica identidad por DNI y, si ok, devuelve token + detalle. Recibe codigo y {dni}."""
    codigo = codigo.upper()
    p = repo.pedido_por_codigo(db, codigo)
    if not p:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    verif.verificar_dni(db, codigo, datos.dni, p.dni_destinatario)
    token = portal_token.crear_token_persona(codigo)
    return {"token": token, "pedido": portal_service.detalle_pedido(db, codigo)}


@router.get("/pedidos/{codigo}")
def detalle(codigo: str, _=Depends(portal_token.requiere_token_persona), db: Session = Depends(get_db)):
    """Detalle completo del pedido (requiere token de persona). Recibe el codigo en la ruta."""
    return portal_service.detalle_pedido(db, codigo.upper())


@router.post("/pedidos/{codigo}/reprogramar")
def reprogramar(codigo: str, datos: Reprogramar, _=Depends(portal_token.requiere_token_persona), db: Session = Depends(get_db)):
    """Registra una solicitud de reprogramacion (nota + notificacion al admin). Recibe codigo y {franja}."""
    return portal_service.registrar_reprogramacion(db, codigo.upper(), datos.franja)


@router.get("/pedidos/{codigo}/pod")
def pod(codigo: str, _=Depends(portal_token.requiere_token_persona), db: Session = Depends(get_db)):
    """Sirve la foto POD SOLO con token de persona. Recibe el codigo en la ruta."""
    p = repo.pedido_por_codigo(db, codigo.upper())
    if not p:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    ev = repo.evidencia_de(db, p.id)
    if not ev or not ev.url_foto:
        raise HTTPException(status_code=404, detail="Sin evidencia disponible")
    # url_foto suele ser '/media/evidencias/archivo.jpg' -> mapear a uploads/.
    # Se resuelve a ruta canonica y se exige que quede DENTRO de uploads/ (defensa
    # contra path traversal si url_foto trajera '..' o una ruta absoluta).
    base = os.path.realpath("uploads")
    rel = ev.url_foto.replace("/media/", "", 1).lstrip("/")
    ruta = os.path.realpath(os.path.join(base, rel))
    if not (ruta == base or ruta.startswith(base + os.sep)) or not os.path.isfile(ruta):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    return FileResponse(ruta)


@router.post("/empresa/login", dependencies=[Depends(limite_publico(10, 60))])
def empresa_login(datos: EmpresaLogin, db: Session = Depends(get_db)):
    """Valida credenciales de empresa y envia OTP por correo. Recibe {codigoAcceso, clave}."""
    cod = datos.codigoAcceso.strip().upper()
    cliente = repo.cliente_por_codigo_acceso(db, cod)
    if not cliente or not cliente.acceso_activo or not cliente.clave_hash or not verify_password(datos.clave, cliente.clave_hash):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    otp = verif.emitir_otp(db, "EMPRESA", cod)
    enviado = correo_service.enviar_simple(
        cliente.correo_portal, "Codigo de acceso al portal SAVA",
        f"Su codigo de verificacion es: {otp}\n\nExpira en 10 minutos.")
    return portal_service.respuesta_login_empresa(
        enviado, otp, enmascarado.mask_correo(cliente.correo_portal), settings.PORTAL_OTP_DEMO)


@router.post("/empresa/verificar", dependencies=[Depends(limite_publico(10, 60))])
def empresa_verificar(datos: EmpresaVerificar, db: Session = Depends(get_db)):
    """Valida el OTP de empresa y devuelve token + datos. Recibe {codigoAcceso, otp}."""
    cod = datos.codigoAcceso.strip().upper()
    cliente = repo.cliente_por_codigo_acceso(db, cod)
    if not cliente:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    verif.verificar_otp(db, "EMPRESA", cod, datos.otp, bloqueo_seg=45)
    token = portal_token.crear_token_empresa(cod)
    nombre = cliente.razon_social
    ini = (nombre or "?")[0].upper()
    return {"token": token, "empresa": {"nombre": nombre, "ini": ini}}


@router.get("/empresa/pedidos")
def empresa_pedidos(cod: str = Depends(portal_token.requiere_token_empresa), db: Session = Depends(get_db)):
    """Filas + contadores de los pedidos de hoy del cliente (requiere token). Sin input extra."""
    cliente = repo.cliente_por_codigo_acceso(db, cod)
    if not cliente:
        raise HTTPException(status_code=401, detail="Sesion invalida")
    return portal_service.tabla_empresa(db, cliente.id)


@router.post("/contacto", dependencies=[Depends(limite_publico(5, 60))])
def contacto(datos: ContactoIn, db: Session = Depends(get_db)):
    """Registra un lead de contacto del landing. Recibe ContactoIn."""
    return publico_forms_service.registrar_contacto(db, datos)


@router.post("/reclamos", dependencies=[Depends(limite_publico(5, 60))])
def reclamos(datos: ReclamoIn, db: Session = Depends(get_db)):
    """Registra un reclamo/queja del Libro de Reclamaciones. Recibe ReclamoIn. Devuelve {codigo}."""
    return publico_forms_service.registrar_reclamo(db, datos)
