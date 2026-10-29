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
    latitud_longitud_captura = Column(String(60), nullable=True)  # "lat,lng" donde se tomo la foto (C26-01)
    receptor_nombre = Column(String(120), nullable=True)          # quien recibio el paquete (C26-02)
    receptor_documento = Column(String(12), nullable=True)        # DNI o CE de quien recibio
    fecha_hora = Column(DateTime, default=datetime.utcnow)
