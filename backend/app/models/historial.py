from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.db.database import Base


class HistorialPedido(Base):
    __tablename__ = "historial_pedidos"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), unique=True, index=True, nullable=True)  # legible: HP-001
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False, index=True)
    estado_anterior = Column(String(50), nullable=True)   # None en el primer evento (creación)
    estado_nuevo = Column(String(50), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)  # quién hizo el cambio
    fecha_utc = Column(DateTime, nullable=False, default=datetime.utcnow)
