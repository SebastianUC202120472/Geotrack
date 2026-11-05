# Esquemas del directorio de mecanicos, su verificacion, la asignacion de un auxilio y las plantillas.
from typing import Optional

from pydantic import BaseModel, Field


class MecanicoBase(BaseModel):
    """Datos de un mecanico o proveedor de auxilio."""
    nombre: str = Field(..., min_length=2, max_length=120)
    empresa_taller: Optional[str] = Field(None, max_length=150)
    tipo_servicio: str = Field(..., max_length=50)  # Mecánico | Grúa | Combustible | Vehículo de reemplazo | Otro
    distritos: str = ""
    direccion: Optional[str] = Field(None, max_length=255)
    latitud: Optional[float] = Field(None, ge=-90, le=90)
    longitud: Optional[float] = Field(None, ge=-180, le=180)
    telefono_whatsapp: str = Field(..., min_length=7, max_length=30)
    telegram_chat_id: Optional[str] = Field(None, max_length=50)
    horario_inicio: str = "08:00"
    horario_fin: str = "20:00"
    activo: bool = True


class MecanicoCreate(MecanicoBase):
    """Alta de un mecanico."""


class MecanicoUpdate(MecanicoBase):
    """Edicion de un mecanico."""


class MecanicoVerificarOtp(BaseModel):
    """Codigo de verificacion que recibio el mecanico."""
    codigo: str = Field(..., max_length=10)


class AsignarMecanico(BaseModel):
    """Mecanico al que el administrador envia el auxilio."""
    mecanico_id: int


class PlantillaUpdate(BaseModel):
    """Texto y estado (encendido/apagado) de la plantilla de un aviso."""
    asunto: Optional[str] = Field(None, max_length=200)
    cuerpo: str = Field(..., max_length=2000)
    activo: bool = True
