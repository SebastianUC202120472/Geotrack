# app/models/conductor.py
# ============================================================================
# CAPA: MODELO (tabla de base de datos) — Perfil del conductor
# ----------------------------------------------------------------------------
# ¿QUÉ HACE?  Guarda los datos personales del conductor (nombre, teléfono, DNI).
#             Va en una tabla aparte, ligada 1:1 al usuario, para NO modificar la
#             tabla 'usuarios' (la autenticación sigue igual) y porque create_all
#             crea tablas nuevas pero no altera las existentes.
# ¿CON QUÉ SE CONECTA?
#   - 'usuario_id' apunta a usuarios.id (el conductor es un Usuario rol='conductor').
#   - La consultan: repositories/conductor_repository.py y conductor_service.py.
# ============================================================================
from sqlalchemy import Column, Integer, String, ForeignKey
from app.db.database import Base


class PerfilConductor(Base):
    __tablename__ = "conductor_perfiles"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), unique=True, nullable=False, index=True)
    nombre = Column(String(120), nullable=False)
    telefono = Column(String(30), nullable=True)
    dni = Column(String(20), nullable=True)
