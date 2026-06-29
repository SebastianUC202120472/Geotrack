# app/models/pedido.py
# Define la tabla 'pedidos'.
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from app.db.database import Base


class Pedido(Base):
    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), unique=True, index=True, nullable=True)        # PD-001 (tracking real / QR)
    referencia_externa = Column(String(50), index=True, nullable=True)         # id del Excel del cliente (opcional)

    # --- Cliente que ENVÍA (empresa) ---
    cliente_id = Column(Integer, ForeignKey("clientes_corporativos.id"), nullable=True, index=True)
    cliente_origen = Column(String(100), nullable=False)  # snapshot del nombre del cliente

    direccion_destino = Column(String(255), nullable=False)

    # --- Destinatario que RECIBE (persona) ---
    nombre_destinatario = Column(String(120), nullable=True)
    telefono_destinatario = Column(String(30), nullable=True)
    dni_destinatario = Column(String(20), nullable=True)

    distrito = Column(String(100), nullable=True)   # se rellena al geocodificar (CUS-16)
    latitud = Column(Float, nullable=True)          # coordenada (CUS-15)
    longitud = Column(Float, nullable=True)
    peso_kg = Column(Float, nullable=True)
    volumen_m3 = Column(Float, nullable=True)
    # POR_RECOGER -> OBSERVADO (faltante en almacén) | LISTO_PARA_ENVIO -> ASIGNADO -> EN_RUTA
    #   -> ENTREGADO / FALLIDO. (Otros: GEOCODIFICACION_FALLIDA, CANCELADO)
    estado = Column(String(50), default="LISTO_PARA_ENVIO")
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_entrega = Column(DateTime, nullable=True)  # se sella al marcar ENTREGADO (CUS-26)

    # --- Recojo de origen ---
    recojo_id = Column(Integer, ForeignKey("solicitudes_recojo.id"), nullable=True, index=True)  # de qué recojo salió
    validado_en = Column(DateTime, nullable=True)   # sello al validar en almacén
    validado_por = Column(Integer, nullable=True)   # id del usuario de almacén que validó
