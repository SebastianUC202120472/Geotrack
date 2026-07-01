from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from app.db.database import Base


class Pedido(Base):
    """Tabla de pedidos de entrega."""

    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), unique=True, index=True, nullable=True)        # codigo de tracking (PD-001...)
    referencia_externa = Column(String(50), index=True, nullable=True)         # id del Excel del cliente

    cliente_id = Column(Integer, ForeignKey("clientes_corporativos.id"), nullable=True, index=True)
    cliente_origen = Column(String(100), nullable=False)  # snapshot del nombre del cliente

    direccion_destino = Column(String(255), nullable=False)

    nombre_destinatario = Column(String(120), nullable=True)
    telefono_destinatario = Column(String(30), nullable=True)
    dni_destinatario = Column(String(20), nullable=True)

    distrito = Column(String(100), nullable=True)   # se rellena al geocodificar
    latitud = Column(Float, nullable=True)
    longitud = Column(Float, nullable=True)
    peso_kg = Column(Float, nullable=True)
    volumen_m3 = Column(Float, nullable=True)
    estado = Column(String(50), default="LISTO_PARA_ENVIO")  # ciclo: POR_RECOGER -> ... -> ENTREGADO / FALLIDO
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_entrega = Column(DateTime, nullable=True)  # se sella al marcar ENTREGADO

    recojo_id = Column(Integer, ForeignKey("solicitudes_recojo.id"), nullable=True, index=True)
    validado_en = Column(DateTime, nullable=True)   # sello al validar en almacen
    validado_por = Column(Integer, nullable=True)   # id del usuario de almacen que valido
