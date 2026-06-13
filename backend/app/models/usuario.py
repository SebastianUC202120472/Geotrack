# app/models/usuario.py
# ============================================================================
# CAPA: MODELO (tabla de base de datos) — Clean Architecture
# ----------------------------------------------------------------------------
# ¿QUÉ HACE?  Define la tabla 'usuarios' en PostgreSQL usando SQLAlchemy.
#             Cada atributo de la clase = una columna de la tabla.
# ¿CON QUÉ SE CONECTA?
#   - Hereda de 'Base' (db/database.py) para que SQLAlchemy la reconozca.
#   - La consultan: repositories/usuario_repository.py y api/deps.py.
# ============================================================================
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from app.db.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"  # nombre real de la tabla en la BD

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), unique=True, index=True, nullable=True)  # legible: AD-001 / CO-001 (según rol)
    correo = Column(String(100), unique=True, index=True, nullable=False)  # login (único)
    hash_contrasena = Column(String(255), nullable=False)  # contraseña ENCRIPTADA (nunca en texto)
    rol = Column(String(20), nullable=False)               # 'admin' (Web) o 'conductor' (App Móvil)
    estado = Column(Boolean, default=True)                 # True = activo; False = deshabilitado
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
