# app/services/usuario_service.py
# Contiene las REGLAS del registro y el login (CUS-01 y CUS-02).
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories import usuario_repository, solicitud_restablecimiento_repository
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, PersonalCreate, PersonalUpdate, PersonalResetContrasena
from app.services import notificaciones_service

# Mensaje genérico para la solicitud de restablecimiento: SIEMPRE el mismo, exista o
# no el correo, para no revelar qué cuentas están registradas (anti-enumeración).
MENSAJE_SOLICITUD = "Si el correo corresponde a un conductor, el administrador recibió tu solicitud y te contactará con tu nueva contraseña."


def registrar_usuario(db: Session, datos: UsuarioCreate) -> Usuario:
    """
    CUS-01: registra un usuario nuevo.
    1) Comprueba que el correo no esté ya en uso.
    2) Encripta la contraseña (nunca se guarda en texto plano).
    3) Pide al repositorio que lo guarde.
    """
    if usuario_repository.obtener_por_correo(db, datos.correo):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo ya está registrado",
        )

    hash_contrasena = get_password_hash(datos.contrasena)
    # datos.rol es un Enum (RolUsuario); guardamos su valor de texto ('admin'/'conductor').
    return usuario_repository.crear_usuario(
        db, correo=datos.correo, hash_contrasena=hash_contrasena, rol=datos.rol.value
    )


def crear_admin_inicial(db: Session, correo: str, contrasena: str) -> None:
    """
    Crea un usuario admin "semilla" al arrancar SI no existe ya.
    Esto resuelve el problema del huevo y la gallina: como el registro está
    cerrado (solo admin), necesitamos un primer admin para poder entrar.
    Sus credenciales vienen de variables de entorno (ADMIN_EMAIL/ADMIN_PASSWORD).
    """
    if not correo or not contrasena:
        return
    if usuario_repository.obtener_por_correo(db, correo):
        return  # ya existe, no lo recreamos
    usuario_repository.crear_usuario(
        db, correo=correo, hash_contrasena=get_password_hash(contrasena), rol="admin"
    )


def solicitar_restablecimiento(db: Session, correo: str) -> dict:
    """Extra CUS-04: el conductor (que olvidó su clave) pide desde el Login que se la
    restablezcan. Si el correo es de un conductor activo, registra la solicitud
    PENDIENTE; en cualquier caso devuelve el MISMO mensaje genérico para no revelar
    qué correos existen. Recibe: el correo escrito en la app."""
    # Se busca igual que en el login (coincidencia exacta del correo).
    correo = (correo or "").strip()
    usuario = usuario_repository.obtener_por_correo(db, correo)
    if usuario and usuario.rol == "conductor" and usuario.estado:
        solicitud_restablecimiento_repository.crear_o_refrescar(db, usuario.id, correo)
        # Notifica al admin que un conductor solicitó restablecimiento de contraseña.
        try:
            notificaciones_service.registrar(
                db, "restablecimientos", "Restablecimiento solicitado",
                f"Conductor: {correo}", "/conductores")
        except Exception:
            pass
    return {"mensaje": MENSAJE_SOLICITUD}


# --- CUS-03: gestión de usuarios del personal (admin/almacén) ---
def _personal_o_404(db: Session, usuario_id: int) -> Usuario:
    """Devuelve un usuario del PANEL (no conductor) o lanza 404. Los conductores se
    gestionan en su propia sección."""
    usuario = usuario_repository.obtener_por_id(db, usuario_id)
    if usuario is None or usuario.rol == "conductor":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return usuario


def listar_personal(db: Session):
    """CUS-03: lista las cuentas del panel (admin/almacén)."""
    return usuario_repository.listar_personal(db)


def crear_personal(db: Session, datos: PersonalCreate) -> Usuario:
    """CUS-03: crea una cuenta de personal (rol admin/almacén) con su clave hasheada y
    sus datos personales (nombre/dni/teléfono/cargo) opcionales."""
    if usuario_repository.obtener_por_correo(db, datos.correo):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El correo ya está registrado")
    return usuario_repository.crear_usuario(
        db, correo=datos.correo, hash_contrasena=get_password_hash(datos.contrasena), rol=datos.rol.value,
        nombre=datos.nombre, dni=datos.dni, telefono=datos.telefono, cargo=datos.cargo,
    )


def actualizar_personal(db: Session, usuario_id: int, datos: PersonalUpdate, admin_id: int) -> Usuario:
    """CUS-03: cambia el rol y/o el estado (activo) de un usuario del panel. Recibe: id,
    los cambios y el id del admin que pide (para impedir que se modifique a sí mismo y
    quede bloqueado fuera del sistema)."""
    usuario = _personal_o_404(db, usuario_id)
    campos = datos.model_dump(exclude_unset=True)
    # El rol y el estado NO se pueden CAMBIAR sobre uno mismo (evita bloquearse fuera del
    # sistema). Los datos personales sí se pueden editar siempre. Comparamos contra el valor
    # ACTUAL (no la mera presencia): el form siempre reenvía el rol, así que guardar los
    # propios datos personales no debe disparar el bloqueo si el rol/estado no cambió.
    rol_nuevo = campos.get("rol")
    estado_nuevo = campos.get("estado")
    cambia_rol_o_estado = (rol_nuevo is not None and rol_nuevo.value != usuario.rol) or \
                          (estado_nuevo is not None and estado_nuevo != usuario.estado)
    if usuario.id == admin_id and cambia_rol_o_estado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes cambiar tu propio rol ni estado (evita bloquearte fuera del sistema)",
        )
    if "rol" in campos and campos["rol"] is not None:
        usuario_repository.actualizar_rol(db, usuario, campos["rol"].value)
    if "estado" in campos and campos["estado"] is not None:
        usuario_repository.actualizar_estado(db, usuario, campos["estado"])
    # Datos personales (nombre/dni/telefono/cargo): se actualizan los presentes.
    personales = {k: campos[k] for k in ("nombre", "dni", "telefono", "cargo") if k in campos}
    if personales:
        usuario_repository.actualizar_datos_personales(db, usuario, personales)
    db.refresh(usuario)
    return usuario


def restablecer_contrasena_personal(db: Session, usuario_id: int, datos: PersonalResetContrasena) -> dict:
    """CUS-03: el admin fija una nueva contraseña a un usuario del panel."""
    usuario = _personal_o_404(db, usuario_id)
    usuario_repository.actualizar_hash(db, usuario.id, get_password_hash(datos.contrasena))
    return {"mensaje": "Contraseña restablecida correctamente"}


def autenticar_y_generar_token(db: Session, correo: str, contrasena: str) -> str:
    """
    CUS-02: valida las credenciales y devuelve un token JWT.
    El token lleva 'sub' (correo) y 'rol', que luego usa deps.py para
    saber quién pide cada endpoint y con qué permisos.
    """
    usuario = usuario_repository.obtener_por_correo(db, correo)

    # Si el usuario no existe O la contraseña no coincide -> 401.
    if not usuario or not verify_password(contrasena, usuario.hash_contrasena):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return create_access_token(data={"sub": usuario.correo, "rol": usuario.rol})
