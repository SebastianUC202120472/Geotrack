from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories import usuario_repository, solicitud_restablecimiento_repository
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, PersonalCreate, PersonalUpdate, PersonalResetContrasena, CambioContrasenaPropia
from app.services import notificaciones_service
from app.core import produccion

# Mensaje genérico anti-enumeración: igual exista o no el correo.
MENSAJE_SOLICITUD = "Si el correo corresponde a una cuenta activa, el administrador recibió tu solicitud y te contactará con tu nueva contraseña."

# A dónde lleva el aviso de la campana según el rol de quien pide la clave.
_RUTA_AVISO = {"conductor": "/conductores", "admin": "/usuarios", "almacen": "/usuarios"}
_ETIQUETA_ROL = {"conductor": "Conductor", "admin": "Administrador", "almacen": "Almacén"}


def registrar_usuario(db: Session, datos: UsuarioCreate) -> Usuario:
    """Registra un usuario nuevo. Recibe UsuarioCreate con correo, contraseña y rol."""
    if usuario_repository.obtener_por_correo(db, datos.correo):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo ya está registrado",
        )

    hash_contrasena = get_password_hash(datos.contrasena)
    return usuario_repository.crear_usuario(
        db, correo=datos.correo, hash_contrasena=hash_contrasena, rol=datos.rol.value
    )


def crear_admin_inicial(db: Session, correo: str, contrasena: str) -> None:
    """Crea el admin semilla al arrancar si no existe. Recibe correo y contraseña del env."""
    if not correo or not contrasena:
        return
    if usuario_repository.obtener_por_correo(db, correo):
        return
    usuario_repository.crear_usuario(
        db, correo=correo, hash_contrasena=get_password_hash(contrasena), rol="admin"
    )


def solicitar_restablecimiento(db: Session, correo: str) -> dict:
    """Registra la solicitud de nueva clave de un conductor o del personal del panel (C04-01). Recibe el correo del login."""
    correo = (correo or "").strip()
    usuario = usuario_repository.obtener_por_correo(db, correo)
    if usuario and usuario.estado and usuario.rol in _RUTA_AVISO:
        solicitud_restablecimiento_repository.crear_o_refrescar(db, usuario.id, correo)
        try:
            notificaciones_service.registrar(
                db, "restablecimientos", "Restablecimiento solicitado",
                f"{_ETIQUETA_ROL[usuario.rol]}: {correo}", _RUTA_AVISO[usuario.rol])
        except Exception:
            pass
    return {"mensaje": MENSAJE_SOLICITUD}


def _personal_o_404(db: Session, usuario_id: int) -> Usuario:
    """Devuelve un usuario de panel (no conductor) o lanza 404. Recibe id de usuario."""
    usuario = usuario_repository.obtener_por_id(db, usuario_id)
    if usuario is None or usuario.rol == "conductor":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return usuario


def listar_personal(db: Session):
    """Lista las cuentas del panel (admin/almacen) marcando quién pidió nueva clave. Recibe la sesión."""
    pendientes = solicitud_restablecimiento_repository.ids_pendientes(db)
    personal = usuario_repository.listar_personal(db)
    for usuario in personal:
        usuario.solicito_restablecimiento = usuario.id in pendientes
    return personal


def mi_perfil(usuario: Usuario) -> Usuario:
    """Devuelve el usuario del panel indicando si aún usa la clave de fábrica (EX-01). Recibe el usuario autenticado."""
    usuario.clave_por_defecto = produccion.usa_clave_de_fabrica(usuario)
    return usuario


def cambiar_contrasena_propia(db: Session, usuario: Usuario, datos: CambioContrasenaPropia) -> dict:
    """Cambia la clave del usuario autenticado tras verificar la actual. Recibe sesión, usuario y claves."""
    if not verify_password(datos.actual, usuario.hash_contrasena):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La contraseña actual no es correcta")
    if datos.actual == datos.nueva:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La nueva contraseña debe ser distinta de la actual")
    usuario_repository.actualizar_hash(db, usuario.id, get_password_hash(datos.nueva))
    solicitud_restablecimiento_repository.marcar_atendidas(db, usuario.id)
    return {"mensaje": "Contraseña actualizada"}


def crear_personal(db: Session, datos: PersonalCreate) -> Usuario:
    """Crea cuenta de personal (admin/almacen). Recibe PersonalCreate."""
    if usuario_repository.obtener_por_correo(db, datos.correo):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El correo ya está registrado")
    return usuario_repository.crear_usuario(
        db, correo=datos.correo, hash_contrasena=get_password_hash(datos.contrasena), rol=datos.rol.value,
        nombre=datos.nombre, dni=datos.dni, telefono=datos.telefono, cargo=datos.cargo,
    )


def actualizar_personal(db: Session, usuario_id: int, datos: PersonalUpdate, admin_id: int) -> Usuario:
    """Actualiza rol/estado/correo/datos de un usuario del panel. Recibe id, cambios e id del admin."""
    usuario = _personal_o_404(db, usuario_id)
    campos = datos.model_dump(exclude_unset=True)
    # Compara contra el valor actual para no bloquear al admin si solo edita datos personales.
    rol_nuevo = campos.get("rol")
    estado_nuevo = campos.get("estado")
    cambia_rol_o_estado = (rol_nuevo is not None and rol_nuevo.value != usuario.rol) or \
                          (estado_nuevo is not None and estado_nuevo != usuario.estado)
    if usuario.id == admin_id and cambia_rol_o_estado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes cambiar tu propio rol ni estado (evita bloquearte fuera del sistema)",
        )
    if "correo" in campos and campos["correo"] is not None:
        nuevo_correo = str(campos["correo"]).strip().lower()
        if nuevo_correo != usuario.correo:
            existente = usuario_repository.obtener_por_correo(db, nuevo_correo)
            if existente and existente.id != usuario.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El correo ya está registrado por otra cuenta",
                )
            usuario_repository.actualizar_correo(db, usuario, nuevo_correo)
    if "rol" in campos and campos["rol"] is not None:
        usuario_repository.actualizar_rol(db, usuario, campos["rol"].value)
    if "estado" in campos and campos["estado"] is not None:
        usuario_repository.actualizar_estado(db, usuario, campos["estado"])
    personales = {k: campos[k] for k in ("nombre", "dni", "telefono", "cargo") if k in campos}
    if personales:
        usuario_repository.actualizar_datos_personales(db, usuario, personales)
    db.refresh(usuario)
    return usuario


def restablecer_contrasena_personal(db: Session, usuario_id: int, datos: PersonalResetContrasena) -> dict:
    """Fija nueva contraseña a un usuario del panel. Recibe id y PersonalResetContrasena."""
    usuario = _personal_o_404(db, usuario_id)
    usuario_repository.actualizar_hash(db, usuario.id, get_password_hash(datos.contrasena))
    solicitud_restablecimiento_repository.marcar_atendidas(db, usuario.id)
    return {"mensaje": "Contraseña restablecida correctamente"}


def autenticar_y_generar_token(db: Session, correo: str, contrasena: str) -> str:
    """Valida credenciales y devuelve un JWT con sub y rol. Recibe correo y contrasena."""
    usuario = usuario_repository.obtener_por_correo(db, correo)

    if not usuario or not verify_password(contrasena, usuario.hash_contrasena):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Validar si la cuenta se encuentra desactivada (CUS-01 / C01-01)
    if not usuario.estado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cuenta se encuentra inactiva o desactivada",
        )

    return create_access_token(data={"sub": usuario.correo, "rol": usuario.rol})
