# app/repositories/usuario_repository.py
# ============================================================================
# CAPA: REPOSITORIO (acceso a datos) — Clean Architecture
# ----------------------------------------------------------------------------
# ¿QUÉ HACE?  Es la ÚNICA capa que habla directamente con la tabla 'usuarios'.
#             Aquí viven los queries de SQLAlchemy (buscar, insertar...).
# ¿CÓMO?      Recibe una sesión de base de datos (db) y ejecuta consultas.
# ¿CON QUÉ SE CONECTA?
#   - models/usuario.py  -> la tabla 'usuarios' que consulta.
#   - db/database.py     -> de ahí viene la sesión 'db'.
#   - Lo USA: services/usuario_service.py (la lógica de negocio).
# ============================================================================
from typing import Optional
from sqlalchemy.orm import Session

from app.models.usuario import Usuario
from app.core.codigos import asignar_codigo, prefijo_por_rol


def obtener_por_correo(db: Session, correo: str) -> Optional[Usuario]:
    """Busca un usuario por su correo. Devuelve el usuario o None si no existe."""
    return db.query(Usuario).filter(Usuario.correo == correo).first()


def obtener_por_id(db: Session, usuario_id: int) -> Optional[Usuario]:
    """Busca un usuario por su id (lo usa el dashboard para mostrar al conductor)."""
    return db.query(Usuario).filter(Usuario.id == usuario_id).first()


def crear_usuario(db: Session, correo: str, hash_contrasena: str, rol: str) -> Usuario:
    """
    Inserta un usuario nuevo en la base de datos.
    Nota: la contraseña ya llega ENCRIPTADA (el hash lo hace el servicio).
    """
    nuevo = Usuario(correo=correo, hash_contrasena=hash_contrasena, rol=rol)
    db.add(nuevo)                                   # lo prepara para guardar
    asignar_codigo(db, nuevo, prefijo_por_rol(rol))  # codigo legible AD-001 / CO-001
    db.commit()                                     # confirma el cambio en PostgreSQL
    db.refresh(nuevo)                               # recarga el objeto con el id ya asignado
    return nuevo
