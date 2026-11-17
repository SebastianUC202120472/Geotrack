from pydantic_settings import BaseSettings, SettingsConfigDict


# Configuracion del asistente de atencion al cliente (Idea 2); todo se lee de variables de
# entorno (.env del servidor). Las claves de IA viven SOLO aqui: nunca llegan al navegador.
# Es independiente del asistente del panel (Idea 1): cada uno se apaga con su propia variable.
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Interruptor general del modulo. En false el servicio responde 503 y el widget no aparece.
    ATENCION_ENABLED: bool = False

    # Base de datos propia del modulo (sus tablas viven en un esquema aparte).
    ATENCION_DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/geotrack"
    ATENCION_DB_SCHEMA: str = "atencion"   # vacio = sin esquema (pruebas con SQLite)

    # API publica del portal en el nucleo (rastrear, reprogramar, contacto). Semana 14.
    ATENCION_CORE_API_URL: str = "http://backend:8000/api"
    ATENCION_CORE_TIMEOUT_SEG: float = 15.0

    # Origenes del sitio que pueden usar el chat (CORS y control de la cabecera Origin).
    # Vacio = no se controla el origen (solo para pruebas locales).
    ATENCION_CORS_ORIGINS: str = ""
    # Dominios a los que el asistente puede enlazar. Cualquier otro enlace se quita de la respuesta.
    ATENCION_DOMINIOS_PERMITIDOS: str = "sava.pe,www.sava.pe"

    # Secreto con el que se firman los tokens de conversacion. Vacio = se genera uno al
    # arrancar (las conversaciones abiertas se pierden al reiniciar el contenedor).
    ATENCION_SECRETO_CONVERSACION: str = ""
    ATENCION_CONVERSACION_VENCE_MIN: int = 120

    # Orden de respaldo de los proveedores de IA. Nombres: gemini, groq, groq_respaldo, openrouter,
    # ollama, anthropic y openai (los que no tengan clave o modelo se omiten solos).
    ATENCION_PROVEEDORES: str = "groq,groq_respaldo,gemini,openrouter,ollama"

    # Claves propias del modulo. Vacias = se usan las mismas del asistente del panel
    # (GEMINI_API_KEY, GROQ_API_KEY, OPENROUTER_API_KEY), por decision del gerente.
    ATENCION_GEMINI_API_KEY: str = ""
    ATENCION_GROQ_API_KEY: str = ""
    ATENCION_OPENROUTER_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""

    ATENCION_GEMINI_MODELO: str = "gemini-3.5-flash-lite"
    ATENCION_GEMINI_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai"
    ATENCION_GROQ_MODELO: str = "openai/gpt-oss-120b"
    ATENCION_GROQ_MODELO_RESPALDO: str = "openai/gpt-oss-20b"
    ATENCION_GROQ_URL: str = "https://api.groq.com/openai/v1"
    ATENCION_OPENROUTER_MODELO: str = "nvidia/nemotron-3.5-super-vl:free"
    ATENCION_OPENROUTER_URL: str = "https://openrouter.ai/api/v1"
    ATENCION_OLLAMA_URL: str = ""
    ATENCION_OLLAMA_MODELO: str = "qwen2.5:7b"
    ATENCION_OLLAMA_TIMEOUT_SEG: float = 120.0

    # Proveedores de pago (solo si el gerente lo aprueba para produccion).
    ATENCION_ANTHROPIC_API_KEY: str = ""
    ATENCION_ANTHROPIC_MODELO: str = "claude-haiku-5-5"
    ATENCION_ANTHROPIC_URL: str = "https://api.anthropic.com/v1"
    ATENCION_OPENAI_API_KEY: str = ""
    ATENCION_OPENAI_MODELO: str = "gpt-4o-mini"
    ATENCION_OPENAI_URL: str = "https://api.openai.com/v1"

    # Tiempos con los proveedores de IA (igual que en la Idea 1).
    ATENCION_IA_TIMEOUT_SEG: float = 20.0
    ATENCION_IA_PRIMER_FRAGMENTO_SEG: float = 15.0
    ATENCION_IA_CONEXION_SEG: float = 5.0
    ATENCION_MAX_TOKENS_RESPUESTA: int = 700
    ATENCION_TEMPERATURA: float = 0.3

    # Limites anti-abuso (el visitante es anonimo).
    ATENCION_MAX_CARACTERES: int = 500
    ATENCION_CONVERSACIONES_POR_HORA_IP: int = 10
    ATENCION_MENSAJES_POR_MINUTO_IP: int = 8
    ATENCION_MENSAJES_POR_DIA_IP: int = 80
    ATENCION_TURNOS_POR_CONVERSACION: int = 30
    ATENCION_TOPE_DIARIO_GLOBAL: int = 1500
    # Tiempo minimo entre abrir la conversacion y el primer mensaje (un bot suele ser instantaneo).
    ATENCION_SEG_MINIMOS_PRIMER_MENSAJE: float = 1.5
    ATENCION_TURNOS_MEMORIA: int = 8
    ATENCION_MAX_RONDAS_FUNCIONES: int = 3

    # Funciones con el portal (semana 14).
    # Verificaciones por DNI por conversacion (el nucleo ademas bloquea por pedido tras 3 fallos).
    ATENCION_VERIFICACIONES_POR_CONVERSACION: int = 6
    # Reprogramaciones y contactos confirmados por conversacion (anti-abuso del nucleo).
    ATENCION_ACCIONES_POR_CONVERSACION: int = 3
    # Minutos que dura una propuesta (tarjeta con Confirmar/Cancelar) sin confirmar.
    ATENCION_PROPUESTA_VENCE_SEG: int = 600
    # Mensajes seguidos sin poder resolver antes de ofrecer hablar con una persona.
    ATENCION_DERIVAR_TRAS_FALLOS: int = 2

    # Voz: Whisper de Groq en el servidor (misma clave de Groq). Sin clave, el widget usa el
    # dictado del navegador (Web Speech API). El audio se procesa en memoria y se descarta.
    ATENCION_VOZ_MODELO: str = "whisper-large-v3-turbo"
    ATENCION_VOZ_MAX_SEG: int = 60
    ATENCION_VOZ_MAX_KB: int = 1024
    ATENCION_AUDIOS_POR_MINUTO_IP: int = 4
    ATENCION_AUDIOS_POR_CONVERSACION: int = 10

    # Base de conocimiento: cuantos articulos se entregan al modelo y puntaje minimo para usarlos.
    ATENCION_KB_RESULTADOS: int = 3
    ATENCION_KB_PUNTAJE_MINIMO: float = 1.0

    # Privacidad (Ley 29733): las conversaciones mas antiguas que esto se borran solas.
    ATENCION_RETENCION_DIAS: int = 30
    ATENCION_PURGA_CADA_MIN: int = 60

    ZONA_HORARIA: str = "America/Lima"

    @staticmethod
    def _lista(valor: str) -> list[str]:
        """Convierte un texto separado por comas en lista sin vacios. Recibe el texto."""
        return [v.strip() for v in (valor or "").split(",") if v.strip()]

    @property
    def lista_proveedores(self) -> list[str]:
        """Proveedores en el orden de ATENCION_PROVEEDORES, en minusculas. Sin input."""
        return [p.lower() for p in self._lista(self.ATENCION_PROVEEDORES)]

    @property
    def cors_origins_list(self) -> list[str]:
        """Origenes permitidos del sitio. Sin input."""
        return [o.rstrip("/") for o in self._lista(self.ATENCION_CORS_ORIGINS)]

    @property
    def dominios_permitidos(self) -> list[str]:
        """Dominios a los que se puede enlazar, en minusculas. Sin input."""
        return [d.lower() for d in self._lista(self.ATENCION_DOMINIOS_PERMITIDOS)]

    @property
    def esquema_db(self) -> str | None:
        """Esquema de las tablas propias o None si no se usa. Sin input."""
        return self.ATENCION_DB_SCHEMA.strip() or None

    @property
    def clave_gemini(self) -> str:
        """Clave propia de Gemini o, si esta vacia, la del asistente del panel. Sin input."""
        return self.ATENCION_GEMINI_API_KEY or self.GEMINI_API_KEY

    @property
    def clave_groq(self) -> str:
        """Clave propia de Groq o, si esta vacia, la del asistente del panel. Sin input."""
        return self.ATENCION_GROQ_API_KEY or self.GROQ_API_KEY

    @property
    def clave_openrouter(self) -> str:
        """Clave propia de OpenRouter o, si esta vacia, la del asistente del panel. Sin input."""
        return self.ATENCION_OPENROUTER_API_KEY or self.OPENROUTER_API_KEY


settings = Settings()
