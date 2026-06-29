# app/schemas/incidencia.py
# Moldes de datos de las INCIDENCIAS (CUS-30: auxilio mecánico).
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class IncidenciaCreate(BaseModel):
    """ENTRADA: el conductor reporta una avería desde la app. La ruta se deduce de su
    ruta activa (no se envía). tipo/descripcion/coordenadas son opcionales."""
    tipo: Optional[str] = "AVERIA_MECANICA"
    descripcion: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    # El conductor indica si puede resolverla él mismo (el admin no necesita mandar ayuda).
    puede_solucionar_solo: Optional[bool] = False


class ResolverIncidenciaRequest(BaseModel):
    """ENTRADA: nota opcional al reanudar la incidencia (solo el conductor cierra)."""
    nota: Optional[str] = None


class MandarAyudaRequest(BaseModel):
    """ENTRADA (admin): el tipo de ayuda a enviar (adaptable a lo que necesita el conductor)
    + una nota opcional. No resuelve la incidencia."""
    tipo: str                       # ej. Mecánico | Grúa | Combustible | Vehículo de reemplazo | Otro
    nota: Optional[str] = None


class IncidenciaResponse(BaseModel):
    """SALIDA: la incidencia tal como la ven la app y el panel."""
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
