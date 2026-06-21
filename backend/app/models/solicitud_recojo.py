# app/models/solicitud_recojo.py
# Define la tabla 'solicitudes_recojo' (módulo Inbound, CUS-10/11/12).
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from app.db.database import Base


class SolicitudRecojo(Base):
    __tablename__ = "solicitudes_recojo"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), unique=True, index=True, nullable=True)   # legible: RC-001

    # Cliente corporativo (retail) que solicita el recojo. Obligatorio.
    cliente_id = Column(Integer, ForeignKey("clientes_corporativos.id"), nullable=False, index=True)
    cliente_origen = Column(String(150), nullable=False)   # snapshot de la razón social

    direccion_origen = Column(String(255), nullable=False)  # dónde recoger (almacén/tienda)
    distrito = Column(String(100), nullable=True)           # se rellena al geocodificar (CUS-16)
    latitud = Column(Float, nullable=True)
    longitud = Column(Float, nullable=True)

    volumen_estimado_m3 = Column(Float, nullable=True)      # CUS-10: volumen estimado de carga
    contacto_origen = Column(String(100), nullable=True)    # persona/teléfono en el punto
    referencia = Column(String(120), nullable=True)         # nº de aviso / nota del cliente

    # SOLICITADO -> ASIGNADO -> EN_RUTA -> RECOGIDO
    estado = Column(String(50), default="SOLICITADO")

    cantidad_declarada = Column(Integer, nullable=True)     # CUS-12: bultos declarados (a bulto cerrado)
    url_guia = Column(String(255), nullable=True)           # CUS-12: foto Guía de Remisión (/media/guias)

    ruta_id = Column(Integer, ForeignKey("rutas.id"), nullable=True, index=True)  # ruta de recojo
    secuencia = Column(Integer, nullable=True)              # orden dentro de la ruta (lo fija el optimizador)

    conversacion_id = Column(Integer, ForeignKey("correo_conversaciones.id"), nullable=True)  # atajo Bandeja

    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_recojo = Column(DateTime, nullable=True)          # se sella al pasar a RECOGIDO
