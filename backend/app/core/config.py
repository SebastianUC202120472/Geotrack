# app/core/config.py
# ============================================================================
# CAPA: CORE / CONFIGURACIÓN — Seguridad (gestión de secretos)
# ----------------------------------------------------------------------------
# ¿QUÉ HACE?  Centraliza TODA la configuración sensible (clave del JWT,
#             credenciales de la BD, orígenes CORS...) y la lee de VARIABLES DE
#             ENTORNO. Así los secretos NO viven en el código (OWASP A02/A05).
# ¿CÓMO?      Usa pydantic-settings: lee variables de entorno y, si existe, del
#             archivo '.env' (que está en .gitignore, no se sube al repo).
#             Si una variable no está definida, usa un valor por defecto SOLO
#             apto para desarrollo (en producción se DEBE sobreescribir).
# ¿CON QUÉ SE CONECTA?
#   - core/security.py -> toma SECRET_KEY/ALGORITHM/expiración del token.
#   - db/database.py   -> toma DATABASE_URL.
#   - main.py          -> toma CORS_ORIGINS y el admin inicial.
# ============================================================================
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Lee del archivo .env si existe; ignora variables extra (ej. POSTGRES_*).
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- JWT / criptografía ---
    SECRET_KEY: str = "dev-inseguro-cambiar-en-produccion"  # nosec B105  (placeholder de desarrollo)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 h para pruebas; reducir en producción

    # --- Base de datos ---
    DATABASE_URL: str = "postgresql://sava_admin:sava_password123@db:5432/siol_sava_db"  # nosec B105

    # --- CORS (orígenes permitidos para el frontend; coma-separado) ---
    CORS_ORIGINS: str = "*"

    # --- Admin inicial (se crea al arrancar si no existe ningún admin) ---
    ADMIN_EMAIL: str = "admin@siol.com"
    ADMIN_PASSWORD: str = "admin123"  # nosec B105  (cambiar por variable de entorno en producción)

    @property
    def cors_origins_list(self) -> list[str]:
        """Convierte 'a.com, b.com' en ['a.com', 'b.com']. '*' permite cualquiera."""
        if not self.CORS_ORIGINS.strip():
            return []
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]


# Instancia única reutilizada en toda la app.
settings = Settings()
