# app/models/ruta.py
# Define DOS tablas relacionadas.
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base


class Ruta(Base):
    __tablename__ = "rutas"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), unique=True, index=True, nullable=True)  # legible: RT-001
    nombre = Column(String(100), nullable=False)  # ej: "Ruta San Miguel - Tarde"
    # Estado de la operación: CREADA -> EN_PROGRESO -> FINALIZADA
    estado = Column(String(50), default="CREADA")
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_fin = Column(DateTime, nullable=True)  # CUS-28: momento del cierre de la ruta

    # Asignaciones (para el MVP las guardamos por id/placa, sin tabla aparte).
    vehiculo_placa = Column(String(20), nullable=True)
    conductor_id = Column(Integer, nullable=True)  # id del Usuario con rol 'conductor'

    # Relación 1-a-muchos: una ruta tiene muchos detalles.
    # cascade="all, delete" -> si se borra la ruta, se borran sus detalles.
    detalles = relationship("RutaDetalle", back_populates="ruta", cascade="all, delete")


class RutaDetalle(Base):
    __tablename__ = "ruta_detalles"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), unique=True, index=True, nullable=True)    # legible: RD-001
    ruta_id = Column(Integer, ForeignKey("rutas.id"), nullable=False)      # a qué ruta pertenece
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)  # qué pedido representa

    # Orden de entrega dentro de la ruta. Lo calcula el VRP (CUS-19).
    secuencia = Column(Integer, nullable=False)

    # Estado de ESTE paquete en la ruta: PENDIENTE -> ENTREGADO / FALLIDO
    estado_entrega = Column(String(50), default="PENDIENTE")

    # --- Fase 3.3: Ejecución y Evidencias ---
    motivo_fallo = Column(String(255), nullable=True)   # CUS-26: razón si fue FALLIDO
    url_evidencia = Column(String(255), nullable=True)  # CUS-29: ruta de la foto POD
    fecha_gestion = Column(DateTime, nullable=True)     # cuándo se entregó/falló

    # Relación inversa: cada detalle pertenece a una ruta.
    ruta = relationship("Ruta", back_populates="detalles")
