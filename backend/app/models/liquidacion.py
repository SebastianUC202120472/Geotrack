from datetime import datetime
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
from app.db.database import Base


class Liquidacion(Base):
    """Registro de liquidaciones generadas por cliente."""

    __tablename__ = "liquidaciones"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes_corporativos.id"), nullable=True, index=True)
    periodo_inicio = Column(Date, nullable=True)
    periodo_fin = Column(Date, nullable=True)
    url_documento = Column(String(255), nullable=False)
    fecha_generacion = Column(DateTime, default=datetime.utcnow)
