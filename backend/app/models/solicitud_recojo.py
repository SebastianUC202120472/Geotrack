from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from app.db.database import Base


# Modelo de la tabla solicitudes_recojo. Representa una solicitud de recojo de un cliente corporativo.
class SolicitudRecojo(Base):
    __tablename__ = "solicitudes_recojo"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), unique=True, index=True, nullable=True)   # legible: RC-001

    cliente_id = Column(Integer, ForeignKey("clientes_corporativos.id"), nullable=False, index=True)
    cliente_origen = Column(String(150), nullable=False)

    direccion_origen = Column(String(255), nullable=False)
    distrito = Column(String(100), nullable=True)
    latitud = Column(Float, nullable=True)
    longitud = Column(Float, nullable=True)

    volumen_estimado_m3 = Column(Float, nullable=True)
    contacto_origen = Column(String(100), nullable=True)    # persona/teléfono en el punto
    referencia = Column(String(120), nullable=True)

    estado = Column(String(50), default="SOLICITADO")

    cantidad_declarada = Column(Integer, nullable=True)
    url_guia = Column(String(255), nullable=True)

    ruta_id = Column(Integer, ForeignKey("rutas.id"), nullable=True, index=True)
    secuencia = Column(Integer, nullable=True)              # orden dentro de la ruta (lo fija el optimizador)

    conversacion_id = Column(Integer, ForeignKey("correo_conversaciones.id"), nullable=True)

    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_recojo = Column(DateTime, nullable=True)          # se sella al pasar a RECOGIDO


# Estados en los que el conductor YA levantó el recojo: recogido, o ya ingresado en
# almacén. Para el conductor ambos cuentan como "recogido" (no pendiente).
ESTADOS_RECOGIDO = ("RECOGIDO", "INGRESADO")
