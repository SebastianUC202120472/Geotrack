# app/models/pedido.py
# ============================================================================
# CAPA: MODELO (tabla de base de datos) — Clean Architecture
# ----------------------------------------------------------------------------
# ¿QUÉ HACE?  Define la tabla 'pedidos': cada paquete que entra al sistema.
# IDENTIFICADORES:
#   - id        -> número interno (llave primaria, para las relaciones).
#   - codigo    -> código LEGIBLE 'PD-001'. Es el identificador del paquete en
#                  nuestro sistema y lo que se imprime/escanea en el QR (CUS-22).
#   - referencia_externa -> el id que viene en el Excel del cliente (opcional);
#                  solo sirve para cruzar datos, NO es nuestro tracking.
# ¿CON QUÉ SE CONECTA?
#   - Hereda de 'Base' (db/database.py). 'cliente_id' -> clientes_corporativos.id.
#   - La consultan: repositories/pedido_repository.py y ruta_repository.py.
# ============================================================================
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
    # PENDIENTE -> ASIGNADO -> EN_RUTA -> ENTREGADO / FALLIDO
    estado = Column(String(50), default="PENDIENTE")
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_entrega = Column(DateTime, nullable=True)  # se sella al marcar ENTREGADO (CUS-26)
