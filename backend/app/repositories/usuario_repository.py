# app/repositories/usuario_repository.py
# Es la ÚNICA capa que habla directamente con la tabla 'usuarios'.
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


def actualizar_hash(db: Session, usuario_id: int, hash_contrasena: str) -> Optional[Usuario]:
    """Reemplaza el hash de la contraseña de un usuario (CUS-04: restablecer clave).
    Recibe: el id del usuario y el hash ya generado por el servicio."""
    usuario = obtener_por_id(db, usuario_id)
    if usuario is None:
        return None
    usuario.hash_contrasena = hash_contrasena
    db.commit()
    db.refresh(usuario)
    return usuario
