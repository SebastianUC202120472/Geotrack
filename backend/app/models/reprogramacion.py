from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.db.database import Base


# Solicitud de reprogramacion que el destinatario hace desde el portal (C43-01). Queda ligada al
# pedido para que el administrador la vea al decidir; puede pedirse antes de la visita (C43-02).
class SolicitudReprogramacion(Base):
    __tablename__ = "solicitudes_reprogramacion"

    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False, index=True)
    franja = Column(String(80), nullable=False)               # "Mañana · 9 am – 1 pm"
    estado = Column(String(20), default="PENDIENTE")          # PENDIENTE | ACEPTADA | RECHAZADA
    creado_en = Column(DateTime, default=datetime.utcnow)
    respuesta = Column(String(255), nullable=True)            # nota del admin al atenderla
    atendida_en = Column(DateTime, nullable=True)
    atendida_por = Column(Integer, nullable=True)             # admin que la atendio
