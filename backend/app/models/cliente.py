# app/models/cliente.py
# ============================================================================
# CAPA: MODELO (tabla de base de datos) — Clean Architecture
# ----------------------------------------------------------------------------
# ¿QUÉ HACE?  Define la tabla 'clientes_corporativos': la EMPRESA que envía los
#             paquetes (el cliente del operador logístico). Alinea el MVP con la
#             propuesta de tesis, donde el cliente es una entidad propia y no un
#             simple texto dentro del pedido.
# ¿CON QUÉ SE CONECTA?
#   - Hereda de 'Base' (db/database.py).
#   - 'pedidos.cliente_id' apunta aquí (un cliente tiene muchos pedidos).
#   - La consultan: repositories/cliente_repository.py y pedido_service.py.
# ============================================================================
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from app.db.database import Base


class ClienteCorporativo(Base):
    __tablename__ = "clientes_corporativos"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), unique=True, index=True, nullable=True)  # legible: CL-001
    razon_social = Column(String(150), nullable=False)            # nombre legal de la empresa
    identificador_unico = Column(String(20), unique=True, index=True, nullable=True)  # RUC (único)
    contacto = Column(String(100), nullable=True)                 # correo/teléfono de contacto
    creado_en = Column(DateTime, default=datetime.utcnow)
    eliminado_en = Column(DateTime, nullable=True)                # borrado lógico (soft delete)
