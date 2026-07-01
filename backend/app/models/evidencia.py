from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.db.database import Base


# Prueba de entrega (POD) de un pedido: foto, firma, geolocalizacion y hora de captura.
class EvidenciaEntrega(Base):
    __tablename__ = "evidencias_entrega"

    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False, index=True)
    url_foto = Column(String(255), nullable=True)
    url_firma = Column(String(255), nullable=True)
    latitud_longitud_captura = Column(String(60), nullable=True)
    fecha_hora = Column(DateTime, default=datetime.utcnow)
