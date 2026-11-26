import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import httpx

from app.core.config import settings
from app.core.registro import obtener_logger
from app.ia.preparador_imagen import preparar_imagen_para_ia
from app.ia.prompt_vision import (
    EvaluacionVision,
    SYSTEM_PROMPT_VISION,
    USER_PROMPT_VISION,
    parsear_respuesta_vision,
)

_log = obtener_logger("cliente_vision")

# Cooldown temporal en memoria (segundos) cuando un proveedor devuelve 429 o 5xx
_COOLDOWN_SEG = 30.0
_enfriamiento_hasta: Dict[str, float] = {}


@dataclass(frozen=True)
class ProveedorVision:
    nombre: str
    base_url: str
    modelo: str
    api_key: str
    timeout: float


def limpiar_enfriamiento() -> None:
    """Reinicia el estado de cooldown de todos los proveedores (útil en pruebas)."""
    _enfriamiento_hasta.clear()


def construir_proveedores_activos() -> List[ProveedorVision]:
    """Construye la lista ordenada de proveedores configurados según AUDITORIA_PROVEEDORES."""
    catalogo = {
        "gemini": ProveedorVision(
            nombre="gemini",
            base_url=settings.GEMINI_URL.rstrip("/"),
            modelo=settings.GEMINI_MODELO,
            api_key=settings.GEMINI_API_KEY.strip(),
            timeout=settings.IA_TIMEOUT_SEG,
        ),
        "groq": ProveedorVision(
            nombre="groq",
            base_url=settings.GROQ_URL.rstrip("/"),
            modelo=settings.GROQ_MODELO,
            api_key=settings.GROQ_API_KEY.strip(),
            timeout=settings.IA_TIMEOUT_SEG,
        ),
        "openrouter": ProveedorVision(
            nombre="openrouter",
            base_url=settings.OPENROUTER_URL.rstrip("/"),
            modelo=settings.OPENROUTER_MODELO,
            api_key=settings.OPENROUTER_API_KEY.strip(),
            timeout=settings.IA_TIMEOUT_SEG,
        ),
        "ollama": ProveedorVision(
            nombre="ollama",
            base_url=(settings.OLLAMA_URL.rstrip("/") + "/v1") if settings.OLLAMA_URL.strip() else "",
            modelo=settings.OLLAMA_MODELO,
            api_key="ollama",  # Ollama local no requiere clave real
            timeout=settings.OLLAMA_TIMEOUT_SEG,
        ),
    }

    activos: List[ProveedorVision] = []
    orden = [p.strip().lower() for p in settings.AUDITORIA_PROVEEDORES.split(",") if p.strip()]

    for nombre in orden:
        prov = catalogo.get(nombre)
        if not prov:
            continue
        if nombre == "ollama":
            if prov.base_url and prov.modelo:
                activos.append(prov)
        elif prov.api_key and prov.modelo and prov.base_url:
            activos.append(prov)

    return activos


def _llamar_proveedor(
    cliente: httpx.Client,
    proveedor: ProveedorVision,
    data_uri: str,
) -> EvaluacionVision:
    """Ejecuta una petición multimodal al endpoint /chat/completions compatible con OpenAI."""
    url = f"{proveedor.base_url}/chat/completions"
    cabeceras = {
        "Authorization": f"Bearer {proveedor.api_key}",
        "Content-Type": "application/json",
    }
    cuerpo = {
        "model": proveedor.modelo,
        "temperature": 0.1,
        "max_tokens": 1024,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT_VISION},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": USER_PROMPT_VISION},
                    {"type": "image_url", "image_url": {"url": data_uri}},
                ],
            },
        ],
    }

    respuesta = cliente.post(url, json=cuerpo, headers=cabeceras, timeout=proveedor.timeout)

    if respuesta.status_code == 429 or respuesta.status_code >= 500:
        raise httpx.HTTPStatusError(
            f"Proveedor {proveedor.nombre} respondió HTTP {respuesta.status_code}",
            request=respuesta.request,
            response=respuesta,
        )

    respuesta.raise_for_status()
    payload = respuesta.json()
    contenido = payload["choices"][0]["message"]["content"]
    return parsear_respuesta_vision(contenido)


def analizar_imagen_con_fallback(
    datos_imagen: bytes,
    http_client: Optional[httpx.Client] = None,
) -> Tuple[Optional[EvaluacionVision], Optional[str]]:
    """Prepara la imagen (downscale + sin EXIF) y la analiza probando proveedores en cascada.
    Devuelve (EvaluacionVision, nombre_proveedor) o (None, None) si ninguno está disponible o todos fallan.
    """
    proveedores = construir_proveedores_activos()
    if not proveedores:
        _log.info("Sin proveedores de visión IA configurados; se mantiene evaluación solo determinística.")
        return None, None

    _, data_uri = preparar_imagen_para_ia(datos_imagen)
    ahora = time.monotonic()

    cliente_propio = http_client is None
    cliente = http_client or httpx.Client()

    try:
        for prov in proveedores:
            if _enfriamiento_hasta.get(prov.nombre, 0.0) > ahora:
                _log.debug("Proveedor %s en cooldown temporal; saltando al siguiente.", prov.nombre)
                continue

            try:
                evaluacion = _llamar_proveedor(cliente, prov, data_uri)
                _log.info("Análisis de visión completado con proveedor '%s'.", prov.nombre)
                return evaluacion, prov.nombre
            except (httpx.TimeoutException, httpx.HTTPStatusError, httpx.RequestError) as exc:
                _enfriamiento_hasta[prov.nombre] = time.monotonic() + _COOLDOWN_SEG
                _log.warning("Fallo con proveedor '%s' (%s). Pasando al siguiente respaldo.", prov.nombre, type(exc).__name__)
            except Exception as exc:
                _log.warning("Respuesta inválida de '%s' (%s). Pasando al siguiente respaldo.", prov.nombre, exc)

        _log.warning("Todos los proveedores de visión IA fallaron o están en cooldown.")
        return None, None
    finally:
        if cliente_propio:
            cliente.close()
