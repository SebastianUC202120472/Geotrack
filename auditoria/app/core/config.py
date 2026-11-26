import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Bandera general del módulo y worker periódico
    AUDITORIA_ENABLED: bool = True
    AUDITORIA_WORKER_ENABLED: bool = True

    # Orígenes CORS permitidos (separados por comas; vacío = solo mismo origen vía Nginx)
    AUDITORIA_CORS_ORIGINS: str = ""

    # Base de datos propia del módulo (tablas viven en esquema 'auditoria')
    # Si AUDITORIA_DATABASE_URL no está definida, toma DATABASE_URL del entorno
    AUDITORIA_DATABASE_URL: str = os.getenv(
        "AUDITORIA_DATABASE_URL",
        os.getenv("DATABASE_URL", "postgresql://sava_admin:sava_password123@db:5432/siol_sava_db")
    )
    AUDITORIA_DB_SCHEMA: str = "auditoria"

    # API del núcleo para validar sesiones y usuarios (solo lectura vía Bearer token)
    CORE_API_URL: str = "http://backend:8000/api"
    CORE_TIMEOUT_SEG: float = 10.0

    # Almacenamiento de archivos
    ALMACENAMIENTO: str = "local"
    UPLOADS_DIR: str = "uploads"
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    SUPABASE_BUCKET: str = "geotrack"

    # Cola, retención y control de consumo diario
    AUDITORIA_TOPE_DIARIO: int = 150
    AUDITORIA_INTERVALO_DETECCION_SEG: int = 30
    AUDITORIA_MAX_REINTENTOS: int = 3
    AUDITORIA_RETENCION_DIAS: int = 90

    # Umbrales determinísticos de calidad y seguridad
    MAX_IMAGE_MB: int = 10
    MAX_PIXELS: int = 25_000_000  # Defensa contra bombas de descompresión (OWASP / DoS)
    MIN_WIDTH: int = 300
    MIN_HEIGHT: int = 300
    BLUR_THRESHOLD: float = 40.0           # Varianza Laplaciana (menor a esto = borrosa)
    DARK_THRESHOLD: float = 45.0           # Brillo promedio < 45 = foto oscura
    OVEREXPOSED_THRESHOLD: float = 235.0   # Brillo promedio > 235 = foto quemada
    HAMMING_DISTANCE_DUPLICATE: int = 5    # Distancia <= 5 en hash de 64 bits = imagen reciclada/duplicada
    MAX_GPS_DISTANCE_METERS: float = 350.0 # Distancia máxima aceptable entre captura y destino
    MAX_TIME_DIFF_MINUTES: float = 120.0   # Tolerancia máxima entre EXIF y hora declarada

    # Proveedores de Visión por IA con fallback
    AUDITORIA_PROVEEDORES: str = "gemini,groq,openrouter,ollama"
    GEMINI_API_KEY: str = ""
    GEMINI_MODELO: str = "gemini-2.5-flash"
    GEMINI_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai"

    GROQ_API_KEY: str = ""
    GROQ_MODELO: str = "llama-3.2-11b-vision-preview"
    GROQ_URL: str = "https://api.groq.com/openai/v1"

    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODELO: str = "meta-llama/llama-3.2-11b-vision-instruct:free"
    OPENROUTER_URL: str = "https://openrouter.ai/api/v1"

    OLLAMA_URL: str = ""
    OLLAMA_MODELO: str = "llama3.2-vision"
    OLLAMA_TIMEOUT_SEG: float = 60.0

    IA_TIMEOUT_SEG: float = 25.0
    IA_IMAGE_MAX_SIZE: int = 1024  # Reducción de resolución previa al envío a IA


settings = Settings()
