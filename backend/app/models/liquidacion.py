# app/models/liquidacion.py
# Define la tabla 'liquidaciones' (CUS-36): cada vez que el admin genera el reporte
# de liquidación de un cliente queda registrado aquí, con el enlace al .xlsx generado.
from datetime import datetime
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
from app.db.database import Base


class Liquidacion(Base):
    __tablename__ = "liquidaciones"

    id = Column(Integer, primary_key=True, index=True)
    # Cliente corporativo al que pertenece la liquidación (NULL si el cliente del
    # snapshot no está registrado como empresa formal).
    cliente_id = Column(Integer, ForeignKey("clientes_corporativos.id"), nullable=True, index=True)
    periodo_inicio = Column(Date, nullable=True)   # rango de fechas cubierto (opcional)
    periodo_fin = Column(Date, nullable=True)
    url_documento = Column(String(255), nullable=False)  # /media/liquidaciones/xxx.xlsx
    fecha_generacion = Column(DateTime, default=datetime.utcnow)  # cuándo se generó
