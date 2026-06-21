# app/services/usuario_service.py
# Contiene las REGLAS del registro y el login (CUS-01 y CUS-02).
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories import usuario_repository, solicitud_restablecimiento_repository
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate

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
    return {"mensaje": MENSAJE_SOLICITUD}


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
