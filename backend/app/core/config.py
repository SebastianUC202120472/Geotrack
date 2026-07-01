from pydantic_settings import BaseSettings, SettingsConfigDict


# Configuracion central de la app; lee variables de entorno desde .env.
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    SECRET_KEY: str = "dev-inseguro-cambiar-en-produccion"  # nosec B105
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    DATABASE_URL: str = "postgresql://sava_admin:sava_password123@db:5432/siol_sava_db"  # nosec B105

    CORS_ORIGINS: str = "*"

    ADMIN_EMAIL: str = "admin@siol.com"
    ADMIN_PASSWORD: str = "admin123"  # nosec B105

    MAIL_ENABLED: bool = False
    MAIL_ADDRESS: str = ""
    MAIL_PASSWORD: str = ""  # nosec B105
    IMAP_HOST: str = "imap.gmail.com"
    IMAP_PORT: int = 993
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    MAIL_FOLDER: str = "INBOX"

    MAIL_FROM_NAME: str = "SAVA S.A.C."
    MAIL_SIGNATURE: str = "Atentamente,\nEquipo de Logística\nSAVA S.A.C."

    @property
    def firma(self) -> str:
        """Devuelve la firma de correo; convierte \\n literales en saltos de linea."""
        base = self.MAIL_SIGNATURE.strip() or "Atentamente,\nEquipo de Logística\nSAVA S.A.C."
        return base.replace("\\n", "\n")

    @property
    def cors_origins_list(self) -> list[str]:
        """Convierte CORS_ORIGINS separado por comas en lista. Recibe el string de origenes."""
        if not self.CORS_ORIGINS.strip():
            return []
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]


settings = Settings()
