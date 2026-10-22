from sqlalchemy import JSON, Column, DateTime, Integer, String, Text

from app.core.fechas import ahora_utc
from app.db.database import Base


class Auditoria(Base):
    """Registro de quien pregunto que, que funciones se ejecutaron y con que resultado."""

    __tablename__ = "auditoria"

    id = Column(Integer, primary_key=True, autoincrement=True)
    creado_en = Column(DateTime, default=ahora_utc, nullable=False, index=True)
    usuario_id = Column(Integer, nullable=False, index=True)
    usuario_correo = Column(String(120), nullable=False)
    rol = Column(String(20), nullable=False)
    conversacion_id = Column(String(32), nullable=True)
    origen = Column(String(10), nullable=False, default="texto")   # texto | voz
    pregunta = Column(Text, nullable=False, default="")             # con DNI y telefonos enmascarados
    funciones = Column(JSON, nullable=True)                         # [{nombre, argumentos, ok}]
    proveedor = Column(String(40), nullable=True)
    resultado = Column(String(20), nullable=False, default="ok")    # ok | error | limite | rechazado
    duracion_ms = Column(Integer, nullable=True)
