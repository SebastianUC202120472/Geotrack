from pydantic import BaseModel
from typing import Optional


class MecanicoBase(BaseModel):
    nombre: str
    empresa_taller: Optional[str] = None
    tipo_servicio: str  # Mecánico | Grúa | Combustible | Vehículo de reemplazo | Otro
    distritos: str = ""
    direccion: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    telefono_whatsapp: str
    telegram_chat_id: Optional[str] = None
    horario_inicio: str = "08:00"
    horario_fin: str = "20:00"
    activo: bool = True


class MecanicoCreate(MecanicoBase):
    pass


class MecanicoUpdate(MecanicoBase):
    pass


class MecanicoVerificarOtp(BaseModel):
    codigo: str


class PlantillaUpdate(BaseModel):
    asunto: Optional[str] = None
    cuerpo: str
    activo: bool = True
