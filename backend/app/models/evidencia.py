# app/models/evidencia.py
# Define la tabla 'evidencias_entrega' (CUS-26): la prueba de entrega (POD) de un
# pedido. Antes la foto solo vivía en ruta_detalles.url_evidencia; ahora queda
# además como registro propio (foto, firma, geolocalización y hora de captura).
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.db.database import Base


class EvidenciaEntrega(Base):
    __tablename__ = "evidencias_entrega"

    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False, index=True)
    url_foto = Column(String(255), nullable=True)    # /media/evidencias/xxx (foto POD)
    url_firma = Column(String(255), nullable=True)   # firma del receptor (Tier 2)
    latitud_longitud_captura = Column(String(60), nullable=True)  # "lat,lng" donde se capturó
    fecha_hora = Column(DateTime, default=datetime.utcnow)  # cuándo se capturó
