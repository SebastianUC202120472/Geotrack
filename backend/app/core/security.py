# app/core/security.py
# ============================================================================
# CAPA: CORE / SEGURIDAD — utilidades transversales
# ----------------------------------------------------------------------------
# ¿QUÉ HACE?  Centraliza la criptografía del sistema:
#               - Encriptar y verificar contraseñas (con Argon2).
#               - Crear y decodificar tokens JWT (la "credencial" del usuario).
# ¿CÓMO?      'passlib' hace el hash de contraseñas; 'jose' firma/verifica el JWT.
# ¿CON QUÉ SE CONECTA?
#   - Lo USAN: services/usuario_service.py (hash + crear token) y
#              api/deps.py (decodificar token para identificar al usuario).
# ============================================================================
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import jwt

from app.core.config import settings

# Contexto de encriptación. Usamos Argon2: estándar moderno y robusto,
# sin problemas de compilación en Windows/Docker.
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# --- Parámetros del token JWT (vienen de variables de entorno via config.py) ---
# Ya NO hay secretos en el código: se leen de la configuración central.
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


def get_password_hash(password: str) -> str:
    """Convierte una contraseña en texto plano a un hash seguro para guardar."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compara la contraseña escrita con el hash guardado. True si coincide."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Genera un token JWT firmado. 'data' lleva la info del usuario (sub=correo, rol).
    Le añade una fecha de expiración ('exp') y lo firma con SECRET_KEY.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Decodifica y valida un token JWT; devuelve su contenido (payload).
    Lanza JWTError si el token es inválido o ya expiró (lo captura deps.py).
    """
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
