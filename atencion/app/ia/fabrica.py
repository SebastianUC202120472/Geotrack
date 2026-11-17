# Traduce la configuracion de ESTE servicio (variables ATENCION_*) a la capa adaptadora de IA,
# que no conoce ninguna variable de entorno.
from app.core.config import Settings, settings
from app.ia.proveedores import CadenaProveedores, ConfigIA, DefinicionProveedor, construir_proveedores


def config_ia(s: Settings = settings) -> ConfigIA:
    """Tiempos y tamano de respuesta para la IA del modulo. Recibe la configuracion."""
    return ConfigIA(
        conexion_seg=s.ATENCION_IA_CONEXION_SEG,
        entre_fragmentos_seg=s.ATENCION_IA_TIMEOUT_SEG,
        primer_fragmento_seg=s.ATENCION_IA_PRIMER_FRAGMENTO_SEG,
        temperatura=s.ATENCION_TEMPERATURA,
        max_tokens=s.ATENCION_MAX_TOKENS_RESPUESTA,
    )


def definiciones(s: Settings = settings) -> dict[str, DefinicionProveedor]:
    """Proveedores que el modulo sabe usar, con su URL, clave y modelo. Recibe la configuracion."""
    ollama_url = s.ATENCION_OLLAMA_URL.rstrip("/") + "/v1" if s.ATENCION_OLLAMA_URL else ""
    return {
        "gemini": DefinicionProveedor("gemini", s.ATENCION_GEMINI_URL, s.clave_gemini, s.ATENCION_GEMINI_MODELO),
        "groq": DefinicionProveedor("groq", s.ATENCION_GROQ_URL, s.clave_groq, s.ATENCION_GROQ_MODELO),
        "groq_respaldo": DefinicionProveedor("groq_respaldo", s.ATENCION_GROQ_URL, s.clave_groq,
                                             s.ATENCION_GROQ_MODELO_RESPALDO),
        "openrouter": DefinicionProveedor("openrouter", s.ATENCION_OPENROUTER_URL, s.clave_openrouter,
                                          s.ATENCION_OPENROUTER_MODELO, {"X-Title": "SAVA Atencion"}),
        "ollama": DefinicionProveedor("ollama", ollama_url, "ollama" if ollama_url else "", s.ATENCION_OLLAMA_MODELO,
                                      plazo_seg=s.ATENCION_OLLAMA_TIMEOUT_SEG),
        "anthropic": DefinicionProveedor("anthropic", s.ATENCION_ANTHROPIC_URL, s.ATENCION_ANTHROPIC_API_KEY,
                                         s.ATENCION_ANTHROPIC_MODELO),
        "openai": DefinicionProveedor("openai", s.ATENCION_OPENAI_URL, s.ATENCION_OPENAI_API_KEY, s.ATENCION_OPENAI_MODELO),
    }


def crear_cadena(s: Settings = settings, orden: list[str] | None = None) -> CadenaProveedores:
    """Arma la cadena de proveedores con respaldo en el orden configurado. Recibe la configuracion y,
    opcionalmente, otro orden (la bateria de ataques elige proveedores por tanda)."""
    return CadenaProveedores(construir_proveedores(orden or s.lista_proveedores, definiciones(s), config_ia(s)))
