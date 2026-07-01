from sqlalchemy import Column, Integer, String, JSON
from app.db.database import Base


# Catalogo de parametros del sistema agrupados por categoria (ej. motivos de rechazo).
class ParametroSistema(Base):
    __tablename__ = "parametros_sistema"

    id = Column(Integer, primary_key=True, index=True)
    categoria = Column(String(50), nullable=False, index=True)
    clave = Column(String(120), nullable=False)
    valor_json = Column(JSON, nullable=True)
