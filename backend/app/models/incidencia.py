# app/models/incidencia.py
# Tabla 'incidencias' (CUS-30): auxilio mecánico que reporta el conductor desde la app
# cuando el vehículo se malogra. Mientras una incidencia de una ruta está ABIERTA, esa
# ruta se considera PAUSADA (no se pueden gestionar paradas ni cerrar el día).
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean, ForeignKey
from app.db.database import Base


class Incidencia(Base):
    __tablename__ = "incidencias"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), unique=True, index=True, nullable=True)  # legible: IN-001
    ruta_id = Column(Integer, ForeignKey("rutas.id"), nullable=False, index=True)
    conductor_id = Column(Integer, nullable=False, index=True)  # usuario que la reporta
    vehiculo_placa = Column(String(20), nullable=True)          # snapshot de la placa de la ruta
    tipo = Column(String(40), default="AVERIA_MECANICA")        # extensible a futuro
    descripcion = Column(Text, nullable=True)                   # detalle del conductor
    url_evidencia = Column(String(255), nullable=True)          # foto de la avería (opcional)
    latitud = Column(Float, nullable=True)                      # dónde ocurrió (opcional)
    longitud = Column(Float, nullable=True)
    estado = Column(String(20), default="ABIERTA")              # ABIERTA | RESUELTA
    creado_en = Column(DateTime, default=datetime.utcnow, index=True)
    resuelto_en = Column(DateTime, nullable=True)
    resuelto_por = Column(Integer, nullable=True)               # SOLO el conductor cierra (reanudar)
    nota_resolucion = Column(String(255), nullable=True)        # ej. "Reanudada por el conductor"

    # El conductor indica al reportar si puede resolverla él mismo (entonces el admin no manda ayuda).
    puede_solucionar_solo = Column(Boolean, default=False)
    # "Mandar ayuda" (admin): sello + detalle adaptable (tipo de ayuda + nota). NO resuelve la incidencia.
    ayuda_enviada_en = Column(DateTime, nullable=True)
    ayuda_enviada_por = Column(Integer, nullable=True)          # usuario_id (admin) que mandó la ayuda
    ayuda_detalle = Column(String(255), nullable=True)          # ej. "Grúa: en 30 min"
