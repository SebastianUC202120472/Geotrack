from pydantic_settings import BaseSettings, SettingsConfigDict


# Configuracion del asistente; todo se lee de variables de entorno (.env del servidor).
# Las claves de los proveedores de IA viven SOLO aqui: nunca llegan al navegador.
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Interruptor general del modulo. En false el servicio responde 503 y el widget no aparece.
    ASISTENTE_ENABLED: bool = False

    # Base de datos propia del modulo (sus tablas viven en un esquema aparte).
    ASISTENTE_DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/geotrack"
    ASISTENTE_DB_SCHEMA: str = "asistente"   # vacio = sin esquema (pruebas con SQLite)

    # API del nucleo: el asistente solo la LEE, con el mismo token del usuario conectado.
    ASISTENTE_CORE_API_URL: str = "http://backend:8000/api"
    ASISTENTE_CORE_TIMEOUT_SEG: float = 15.0

    # Origenes permitidos (solo para desarrollo con Vite; en Docker todo llega por Nginx).
    ASISTENTE_CORS_ORIGINS: str = ""

    # Orden de respaldo de los proveedores de IA: si uno falla o llega a su limite, pasa al siguiente.
    ASISTENTE_PROVEEDORES: str = "gemini,groq,openrouter,ollama"

    GEMINI_API_KEY: str = ""
    GEMINI_MODELO: str = "gemini-2.5-flash"
    GEMINI_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai"

    GROQ_API_KEY: str = ""
    GROQ_MODELO: str = "llama-3.3-70b-versatile"
    GROQ_URL: str = "https://api.groq.com/openai/v1"

    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODELO: str = "meta-llama/llama-3.3-70b-instruct:free"
    OPENROUTER_URL: str = "https://openrouter.ai/api/v1"

    # Ollama corre en la propia PC: no necesita clave. Vacio = desactivado.
    OLLAMA_URL: str = ""
    OLLAMA_MODELO: str = "qwen2.5:7b"

    # Proveedores de pago (solo si el gerente lo aprueba para produccion).
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODELO: str = "claude-haiku-5-5"
    ANTHROPIC_URL: str = "https://api.anthropic.com/v1"
    OPENAI_API_KEY: str = ""
    OPENAI_MODELO: str = "gpt-4o-mini"
    OPENAI_URL: str = "https://api.openai.com/v1"

    ASISTENTE_IA_TIMEOUT_SEG: float = 45.0
    ASISTENTE_MAX_TOKENS_RESPUESTA: int = 2048
    ASISTENTE_TEMPERATURA: float = 0.2

    # Voz: transcripcion en el servidor con Whisper de Groq. Sin clave, el widget usa el
    # dictado del navegador (Web Speech API).
    ASISTENTE_VOZ_MODELO: str = "whisper-large-v3-turbo"
    ASISTENTE_VOZ_MAX_SEG: int = 60
    ASISTENTE_VOZ_MAX_KB: int = 1024

    # Limites de uso por usuario.
    ASISTENTE_MAX_CARACTERES: int = 1000
    ASISTENTE_MENSAJES_POR_MINUTO: int = 10
    ASISTENTE_AUDIOS_POR_MINUTO: int = 5
    ASISTENTE_MENSAJES_POR_DIA: int = 200
    ASISTENTE_MAX_RONDAS_FUNCIONES: int = 5
    ASISTENTE_TURNOS_MEMORIA: int = 12

    # Tope de pedidos que una consulta puede recorrer (paginas de 500 del nucleo).
    ASISTENTE_MAX_PEDIDOS_CONSULTA: int = 5000

    ZONA_HORARIA: str = "America/Lima"

    @property
    def lista_proveedores(self) -> list[str]:
        """Convierte ASISTENTE_PROVEEDORES en lista ordenada. Sin input."""
        return [p.strip().lower() for p in self.ASISTENTE_PROVEEDORES.split(",") if p.strip()]

    @property
    def cors_origins_list(self) -> list[str]:
        """Convierte ASISTENTE_CORS_ORIGINS separado por comas en lista. Sin input."""
        return [o.strip() for o in self.ASISTENTE_CORS_ORIGINS.split(",") if o.strip()]

    @property
    def esquema_db(self) -> str | None:
        """Devuelve el esquema de las tablas propias o None si no se usa. Sin input."""
        return self.ASISTENTE_DB_SCHEMA.strip() or None


settings = Settings()
