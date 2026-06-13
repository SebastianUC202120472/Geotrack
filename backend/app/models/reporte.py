# app/models/reporte.py
# Reporte de incidencia que crea el conductor cuando un pedido falla; el admin lo
# ve y responde con una solución desde el panel web.
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from app.db.database import Base


class Reporte(Base):
    __tablename__ = "reportes"

    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False, index=True)
    pedido_codigo = Column(String(20), nullable=True)      # snapshot PD-001 para mostrar
    conductor_id = Column(Integer, nullable=False, index=True)
    motivo = Column(String(120), nullable=False)           # categoría corta de la falla
    descripcion = Column(Text, nullable=True)              # detalle del conductor
    estado = Column(String(20), default="ABIERTO")         # ABIERTO | RESUELTO
    respuesta = Column(Text, nullable=True)                # solución que escribe el admin
    accion = Column(String(60), nullable=True)             # ej. "Traer a base", "Reprogramar"
    creado_en = Column(DateTime, default=datetime.utcnow, index=True)
    respondido_en = Column(DateTime, nullable=True)
    respondido_por = Column(Integer, nullable=True)        # id del admin que respondió
