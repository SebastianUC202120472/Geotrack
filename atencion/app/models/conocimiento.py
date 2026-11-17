# Base de conocimiento de SAVA (tablas propias). Cada articulo existe por idioma; el par
# espanol/ingles comparte la misma "clave". Cada cambio deja una copia en el historial
# (quien y cuando) para auditar y poder volver atras.
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint

from app.core.fechas import ahora_utc
from app.db.database import Base


class ArticuloConocimiento(Base):
    """Un articulo de la base de conocimiento (una pregunta frecuente o un tema)."""
    __tablename__ = "kb_articulo"
    __table_args__ = (UniqueConstraint("clave", "idioma", name="uq_kb_clave_idioma"),)

    id = Column(Integer, primary_key=True)
    clave = Column(String(80), nullable=False, index=True)       # p. ej. "cobertura-distritos"
    idioma = Column(String(2), nullable=False)                   # es | en
    categoria = Column(String(40), nullable=False, default="general")
    titulo = Column(String(200), nullable=False)
    contenido = Column(Text, nullable=False)
    etiquetas = Column(String(400), nullable=False, default="")  # palabras extra para la busqueda
    activo = Column(Boolean, nullable=False, default=True)
    version = Column(Integer, nullable=False, default=1)
    editado_por = Column(String(120), nullable=False, default="semilla")
    creado_en = Column(DateTime, nullable=False, default=ahora_utc)
    editado_en = Column(DateTime, nullable=False, default=ahora_utc)


class HistorialArticulo(Base):
    """Copia de un articulo en cada version (auditoria de la base de conocimiento)."""
    __tablename__ = "kb_historial"

    id = Column(Integer, primary_key=True)
    articulo_id = Column(Integer, ForeignKey("kb_articulo.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    accion = Column(String(20), nullable=False)                  # CREADO | EDITADO | ACTIVADO | DESACTIVADO
    titulo = Column(String(200), nullable=False)
    contenido = Column(Text, nullable=False)
    etiquetas = Column(String(400), nullable=False, default="")
    activo = Column(Boolean, nullable=False)
    editado_por = Column(String(120), nullable=False)
    editado_en = Column(DateTime, nullable=False, default=ahora_utc)
