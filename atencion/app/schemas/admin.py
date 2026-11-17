# Esquemas de la pantalla de administracion del panel (solo administradores).
import re
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

_CLAVE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def _limpio(v: str) -> str:
    """Quita caracteres de control y espacios sobrantes. Recibe el texto."""
    return _CONTROL.sub("", v or "").strip()


class ArticuloDatos(BaseModel):
    """Campos editables de un articulo."""
    categoria: str = Field(min_length=2, max_length=40)
    titulo: str = Field(min_length=3, max_length=200)
    contenido: str = Field(min_length=10, max_length=3000)
    etiquetas: str = Field(default="", max_length=400)

    @field_validator("categoria", "titulo", "contenido", "etiquetas")
    @classmethod
    def _v_texto(cls, v: str) -> str:
        """Limpia el texto. Recibe el valor."""
        return _limpio(v)

    @field_validator("categoria")
    @classmethod
    def _v_categoria(cls, v: str) -> str:
        """Categoria en minusculas, sin espacios. Recibe la categoria."""
        v = v.lower().replace(" ", "-")
        if not _CLAVE.match(v):
            raise ValueError("La categoría solo admite letras, números y guiones")
        return v


class ArticuloNuevo(ArticuloDatos):
    """Articulo nuevo: ademas lleva su clave e idioma."""
    clave: str = Field(min_length=3, max_length=80)
    idioma: Literal["es", "en"]

    @field_validator("clave")
    @classmethod
    def _v_clave(cls, v: str) -> str:
        """Clave en minusculas con guiones (p. ej. "cobertura-callao"). Recibe la clave."""
        v = _limpio(v).lower()
        if not _CLAVE.match(v):
            raise ValueError("La clave solo admite minúsculas, números y guiones (p. ej. cobertura-callao)")
        return v


class EstadoArticulo(BaseModel):
    """Activar o desactivar un articulo."""
    activo: bool


class ArticuloSalida(BaseModel):
    """Articulo tal como lo ve la administracion."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    clave: str
    idioma: str
    categoria: str
    titulo: str
    contenido: str
    etiquetas: str
    activo: bool
    version: int
    editado_por: str
    editado_en: datetime


class VersionSalida(BaseModel):
    """Una version del historial de un articulo."""
    model_config = ConfigDict(from_attributes=True)

    version: int
    accion: str
    titulo: str
    contenido: str
    activo: bool
    editado_por: str
    editado_en: datetime


class PruebaBusqueda(BaseModel):
    """Pregunta de prueba para ver que articulos recupera el asistente."""
    consulta: str = Field(min_length=2, max_length=300)
    idioma: Literal["es", "en"] = "es"


class MensajeSalida(BaseModel):
    """Mensaje de una conversacion (ya enmascarado)."""
    model_config = ConfigDict(from_attributes=True)

    rol: str
    contenido: str
    origen: str
    modo: Optional[str] = None
    creado_en: datetime


class DerivacionSalida(BaseModel):
    """Fila de la bandeja de derivaciones."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    conversacion_id: str
    origen: str
    motivo: str
    contacto: Optional[str] = None
    idioma: str
    estado: str
    creada_en: datetime
    atendida_por: Optional[str] = None
    atendida_en: Optional[datetime] = None


class DerivacionDetalle(DerivacionSalida):
    """Derivacion con los mensajes de su conversacion."""
    pagina: str = "landing"
    mensajes: list[MensajeSalida] = []
