# app/models/historial.py
# ============================================================================
# CAPA: MODELO (tabla de base de datos) — Clean Architecture
# ----------------------------------------------------------------------------
# ¿QUÉ HACE?  Define la tabla 'historial_pedidos': el REGISTRO DE EVENTOS de
#             cada paquete. Es la columna vertebral de la TRAZABILIDAD (CUS-35):
#             guarda cada cambio de estado, cuándo ocurrió y quién lo hizo.
# ¿POR QUÉ?   Antes la línea de tiempo se "reconstruía" del estado actual; con
#             esta tabla queda un rastro real e inmutable de todo el recorrido.
# ¿CON QUÉ SE CONECTA?
#   - Hereda de 'Base' (db/database.py).
#   - 'pedido_id' -> pedidos.id ; 'usuario_id' -> usuarios.id (quién lo cambió).
#   - La escribe: repositories/historial_repository.py (llamado desde los services).
# ============================================================================
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.db.database import Base


class HistorialPedido(Base):
    __tablename__ = "historial_pedidos"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), unique=True, index=True, nullable=True)  # legible: HP-001
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False, index=True)
    estado_anterior = Column(String(50), nullable=True)   # None en el primer evento (creación)
    estado_nuevo = Column(String(50), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)  # quién hizo el cambio
    fecha_utc = Column(DateTime, nullable=False, default=datetime.utcnow)
