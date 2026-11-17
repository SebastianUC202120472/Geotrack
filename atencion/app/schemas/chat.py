import re
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

from app.core.config import settings

_CONTROL = {chr(c) for c in range(32)} - {"\n", "\t"}


class NuevaConversacion(BaseModel):
    """Inicio de una conversacion: exige aceptar el aviso de privacidad (Ley 29733)."""
    acepta_privacidad: bool
    version_aviso: str = Field(max_length=40)
    idioma: Literal["es", "en"] = "es"
    pagina: Literal["landing", "portal"] = "landing"
    # Honeypot: campo oculto del widget que una persona nunca llena (si llega con texto, es un bot).
    sitio_web: Optional[str] = Field(default=None, max_length=200)


class ConversacionCreada(BaseModel):
    """Token de la conversacion anonima y saludo inicial."""
    token: str
    vence_en_seg: int
    saludo: str


class ChatRequest(BaseModel):
    """Mensaje del visitante. Recibe el texto y si vino por voz."""
    mensaje: str = Field(min_length=1)
    origen: Literal["texto", "voz"] = "texto"

    @field_validator("mensaje")
    @classmethod
    def _v_mensaje(cls, v: str) -> str:
        """Quita caracteres de control y exige texto dentro del largo maximo. Recibe el mensaje."""
        v = "".join(c for c in v if c not in _CONTROL).strip()
        if not v:
            raise ValueError("El mensaje está vacío")
        if len(v) > settings.ATENCION_MAX_CARACTERES:
            raise ValueError(f"El mensaje supera los {settings.ATENCION_MAX_CARACTERES} caracteres")
        return v


class EstadoResponse(BaseModel):
    """Lo que el widget necesita saber para mostrarse."""
    activo: bool
    con_ia: bool
    max_caracteres: int
    version_aviso: str
    voz_servidor: bool = False
    max_seg_voz: int = 60


class AvisoPrivacidad(BaseModel):
    """Aviso de privacidad en el idioma pedido."""
    version: str
    titulo: str
    resumen: str
    puntos: list[str]
    aceptar: str
    enlace_politica: Optional[str] = None


class VerificarRequest(BaseModel):
    """Formulario de verificacion del widget: codigo y los ultimos 4 digitos del DNI del destinatario.
    Este formulario NO pasa por el modelo de IA: va directo al portal y los digitos no se guardan."""
    codigo: str = Field(min_length=3, max_length=30)
    digitos: str = Field(pattern=r"^\d{4}$")


class VerificarResponse(BaseModel):
    """Resultado de la verificacion y el mensaje que el widget envia al chat para seguir."""
    ok: bool
    codigo: str
    mensaje_sugerido: str


class ResultadoAccion(BaseModel):
    """Resultado de confirmar o cancelar una propuesta."""
    id: str
    estado: str
    mensaje: str


class DerivacionRequest(BaseModel):
    """Boton "Hablar con una persona": motivo y, si el visitante quiere, un correo o telefono."""
    motivo: Optional[str] = Field(default=None, max_length=300)
    contacto: Optional[str] = Field(default=None, max_length=120)

    @field_validator("contacto")
    @classmethod
    def _v_contacto(cls, v: Optional[str]) -> Optional[str]:
        """Acepta un correo o un telefono (7 a 15 digitos). Recibe el contacto."""
        if v is None or not v.strip():
            return None
        v = " ".join(v.split())
        es_correo = re.fullmatch(r"[\w.+-]{1,64}@[\w-]{1,63}(\.[\w-]{1,63})+", v)
        es_telefono = re.fullmatch(r"\+?[\d \-]{7,20}", v) and 7 <= len(re.sub(r"\D", "", v)) <= 15
        if not (es_correo or es_telefono):
            raise ValueError("Escribe un correo o un teléfono válido")
        return v


class DerivacionResponse(BaseModel):
    """Confirmacion de que la conversacion quedo en la bandeja del equipo."""
    ok: bool
    mensaje: str


class TranscripcionResponse(BaseModel):
    """Texto que se entendio del mensaje de voz y su idioma."""
    texto: str
    idioma: Optional[str] = None
