from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class IncidenciaCreate(BaseModel):
    """Datos para reportar una avería desde la app. La ruta se deduce de la ruta activa del conductor."""
    tipo: Optional[str] = "AVERIA_MECANICA"
    descripcion: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    puede_solucionar_solo: Optional[bool] = False


class ResolverIncidenciaRequest(BaseModel):
    """Nota opcional al reanudar/cerrar la incidencia."""
    nota: Optional[str] = None


class MandarAyudaRequest(BaseModel):
    """Tipo de ayuda y nota opcional que el admin envía al conductor. Recibe tipo y nota."""
    tipo: str                       # ej. Mecánico | Grúa | Combustible | Vehículo de reemplazo | Otro
    nota: Optional[str] = None


class IncidenciaResponse(BaseModel):
    """Incidencia serializada para la app y el panel."""
    id: int
    codigo: Optional[str] = None
    ruta_id: int
    ruta_nombre: Optional[str] = None
    conductor_id: int
    conductor_nombre: Optional[str] = None
    vehiculo_placa: Optional[str] = None
    tipo: str
    descripcion: Optional[str] = None
    url_evidencia: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    estado: str
    creado_en: Optional[datetime] = None
    resuelto_en: Optional[datetime] = None
    nota_resolucion: Optional[str] = None
    puede_solucionar_solo: bool = False
    ayuda_enviada_en: Optional[datetime] = None
    ayuda_detalle: Optional[str] = None
