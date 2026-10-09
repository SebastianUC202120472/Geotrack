# Revision de la configuracion de produccion (EX-01). Al arrancar, el backend avisa en
# el registro de todo lo que no deberia quedar asi en un despliegue real.
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import verify_password
from app.repositories import usuario_repository

# Clave de fabrica del administrador semilla; esta publicada en el repositorio.
CLAVE_ADMIN_FABRICA = "admin123"  # nosec B105
SECRET_KEY_FABRICA = "dev-inseguro-cambiar-en-produccion"  # nosec B105


def usa_clave_de_fabrica(usuario) -> bool:
    """Dice si la cuenta sigue con la clave de fabrica del admin semilla. Recibe el usuario."""
    if usuario is None or usuario.correo != settings.ADMIN_EMAIL:
        return False
    try:
        return verify_password(CLAVE_ADMIN_FABRICA, usuario.hash_contrasena)
    except Exception:
        return False


def advertencias(db: Session) -> list[str]:
    """Lista lo que falta ajustar para produccion. Recibe una sesion de BD."""
    avisos = []
    if settings.SECRET_KEY == SECRET_KEY_FABRICA:
        avisos.append("SECRET_KEY usa el valor de fábrica: defina una clave larga y aleatoria.")
    if "*" in settings.cors_origins_list:
        avisos.append("CORS_ORIGINS='*' acepta cualquier origen: déjelo vacío (mismo origen vía Nginx) o liste los dominios.")
    if settings.PORTAL_OTP_DEMO:
        avisos.append("PORTAL_OTP_DEMO está encendido: el portal muestra el código OTP en pantalla.")
    if settings.ALMACEN_INGRESO_DIRECTO:
        avisos.append("ALMACEN_INGRESO_DIRECTO está encendido: el almacén recibe sin ruta de recojo ni fotos.")
    if not settings.MAIL_ENABLED:
        avisos.append("MAIL_ENABLED=false: no se envían OTP del portal, constancias ni respuestas de la Bandeja.")
    if usa_clave_de_fabrica(usuario_repository.obtener_por_correo(db, settings.ADMIN_EMAIL)):
        avisos.append(f"La cuenta {settings.ADMIN_EMAIL} sigue con la clave de fábrica: cámbiela desde Mi perfil.")
    return avisos
