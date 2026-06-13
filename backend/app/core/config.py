# app/core/config.py
# Centraliza TODA la configuración sensible (clave del JWT, credenciales de la BD, orígenes CORS...) y la lee de VARIABLES DE ENTORNO.
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

    # --- Correo de la empresa (bandeja de solicitudes de recojo) ---
    # Lee la bandeja por IMAP y envía respuestas por SMTP. Mientras MAIL_ENABLED
    # sea False o falten credenciales, la bandeja funciona en modo "no configurado"
    # (no rompe la app; solo avisa que falta conectar la cuenta).
    # Para Gmail: activa la verificación en 2 pasos y usa una CONTRASEÑA DE APLICACIÓN.
    MAIL_ENABLED: bool = False
    MAIL_ADDRESS: str = ""        # correo base de la empresa (usuario IMAP/SMTP)
    MAIL_PASSWORD: str = ""       # contraseña de aplicación  # nosec B105
    IMAP_HOST: str = "imap.gmail.com"
    IMAP_PORT: int = 993
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    MAIL_FOLDER: str = "INBOX"    # carpeta IMAP a leer

    # Identidad corporativa de las respuestas que se envían desde el panel.
    MAIL_FROM_NAME: str = "SAVA S.A.C."  # nombre visible del remitente
    # Firma que se añade al final de cada respuesta. En .env puedes usar "\n"
    # para los saltos de línea (se convierten al enviar).
    MAIL_SIGNATURE: str = "Atentamente,\nEquipo de Logística\nSAVA S.A.C."

    @property
    def firma(self) -> str:
        """Firma de las respuestas. Si la variable viene vacía, usa una por defecto.
        Convierte los '\\n' (útil al definirla en una sola línea en el .env)."""
        base = self.MAIL_SIGNATURE.strip() or "Atentamente,\nEquipo de Logística\nSAVA S.A.C."
        return base.replace("\\n", "\n")

    @property
    def cors_origins_list(self) -> list[str]:
        """Convierte 'a.com, b.com' en ['a.com', 'b.com']. '*' permite cualquiera."""
        if not self.CORS_ORIGINS.strip():
            return []
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]


# Instancia única reutilizada en toda la app.
settings = Settings()
