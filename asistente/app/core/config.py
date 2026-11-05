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

    # Orden de respaldo de los proveedores de IA: si uno falla, llega a su limite o no responde
    # a tiempo, pasa al siguiente. Nombres validos: gemini, groq, groq_respaldo, openrouter,
    # ollama, anthropic y openai (los que no tengan clave o modelo se omiten solos).
    ASISTENTE_PROVEEDORES: str = "gemini,groq,groq_respaldo,openrouter,ollama"

    GEMINI_API_KEY: str = ""
    GEMINI_MODELO: str = "gemini-3.5-flash-lite"
    GEMINI_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai"

    GROQ_API_KEY: str = ""
    GROQ_MODELO: str = "openai/gpt-oss-120b"
    # Segundo modelo de Groq con la misma clave: Groq pone los limites por modelo, asi que
    # cuando el principal llega a su limite este suele seguir libre. Vacio = sin respaldo.
    GROQ_MODELO_RESPALDO: str = "openai/gpt-oss-20b"
    GROQ_URL: str = "https://api.groq.com/openai/v1"

    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODELO: str = "nvidia/nemotron-3.5-super-vl:free"
    OPENROUTER_URL: str = "https://openrouter.ai/api/v1"

    # Ollama corre en la propia PC: no necesita clave. Vacio = desactivado.
    OLLAMA_URL: str = ""
    OLLAMA_MODELO: str = "qwen2.5:7b"
    # Ollama en una PC sin tarjeta de video tarda mucho mas en empezar: tiene su propio plazo.
    OLLAMA_TIMEOUT_SEG: float = 120.0

    # Proveedores de pago (solo si el gerente lo aprueba para produccion).
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODELO: str = "claude-haiku-5-5"
    ANTHROPIC_URL: str = "https://api.anthropic.com/v1"
    OPENAI_API_KEY: str = ""
    OPENAI_MODELO: str = "gpt-4o-mini"
    OPENAI_URL: str = "https://api.openai.com/v1"

    # Tiempos de espera con los proveedores de IA. TIMEOUT_SEG es la espera maxima entre dos
    # fragmentos de la respuesta; PRIMER_FRAGMENTO_SEG es el plazo para que empiece a llegar
    # algo: si se vence, se pasa al siguiente proveedor sin que el usuario vea nada a medias.
    ASISTENTE_IA_TIMEOUT_SEG: float = 20.0
    ASISTENTE_IA_PRIMER_FRAGMENTO_SEG: float = 20.0
    ASISTENTE_IA_CONEXION_SEG: float = 5.0
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

    # Acciones con confirmacion (OWASP LLM06). El modelo solo PROPONE; el cambio lo hace el clic del
    # usuario en "Confirmar", con su propio token. En false las funciones de accion ni se ofrecen.
    ASISTENTE_ACCIONES_ENABLED: bool = False
    ASISTENTE_ACCION_VENCE_SEG: int = 300
    ASISTENTE_ACCIONES_POR_MINUTO: int = 5

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
