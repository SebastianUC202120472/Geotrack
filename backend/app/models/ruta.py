from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base


class Ruta(Base):
    __tablename__ = "rutas"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), unique=True, index=True, nullable=True)
    nombre = Column(String(100), nullable=False)
    tipo = Column(String(20), default="ENTREGA", server_default="ENTREGA", nullable=False)  # ENTREGA o RECOJO
    estado = Column(String(50), default="CREADA")
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_salida = Column(DateTime, nullable=True)
    fecha_fin = Column(DateTime, nullable=True)
    km_estimado = Column(Float, nullable=True)   # distancia total de la secuencia optimizada
    km_ahorrado = Column(Float, nullable=True)   # km ahorrados vs orden empirico

    vehiculo_placa = Column(String(20), nullable=True)
    conductor_id = Column(Integer, nullable=True)

    detalles = relationship("RutaDetalle", back_populates="ruta", cascade="all, delete")


class RutaDetalle(Base):
    __tablename__ = "ruta_detalles"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), unique=True, index=True, nullable=True)
    ruta_id = Column(Integer, ForeignKey("rutas.id"), nullable=False)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)

    secuencia = Column(Integer, nullable=False)
    estado_entrega = Column(String(50), default="PENDIENTE")

    motivo_fallo = Column(String(255), nullable=True)
    url_evidencia = Column(String(255), nullable=True)   # foto POD
    fecha_gestion = Column(DateTime, nullable=True)

    retornado_en = Column(DateTime, nullable=True)
    retornado_por = Column(Integer, nullable=True)   # id del usuario de almacen que recibio el retorno

    ruta = relationship("Ruta", back_populates="detalles")
