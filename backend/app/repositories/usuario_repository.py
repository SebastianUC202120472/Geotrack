# app/repositories/usuario_repository.py
# Es la ÚNICA capa que habla directamente con la tabla 'usuarios'.
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.usuario import Usuario
from app.core.codigos import asignar_codigo, prefijo_por_rol


def listar_personal(db: Session) -> List[Usuario]:
    """Lista los usuarios del PANEL (admin/almacén), no los conductores.
    Recibe: la sesión. Devuelve la lista ordenada por código."""
    return (
        db.query(Usuario)
        .filter(Usuario.rol != "conductor")
        .order_by(Usuario.codigo.asc())
        .all()
    )


def actualizar_rol(db: Session, usuario: Usuario, rol: str) -> Usuario:
    """Cambia el rol de un usuario. Recibe: el usuario y el nuevo rol (texto)."""
    usuario.rol = rol
    db.commit()
    db.refresh(usuario)
    return usuario


def actualizar_estado(db: Session, usuario: Usuario, estado: bool) -> Usuario:
    """Activa/desactiva un usuario. Recibe: el usuario y el nuevo estado (bool)."""
    usuario.estado = estado
    db.commit()
    db.refresh(usuario)
    return usuario


def obtener_por_correo(db: Session, correo: str) -> Optional[Usuario]:
    """Busca un usuario por su correo. Devuelve el usuario o None si no existe."""
    return db.query(Usuario).filter(Usuario.correo == correo).first()


def obtener_por_id(db: Session, usuario_id: int) -> Optional[Usuario]:
    """Busca un usuario por su id (lo usa el dashboard para mostrar al conductor)."""
    return db.query(Usuario).filter(Usuario.id == usuario_id).first()


def crear_usuario(db: Session, correo: str, hash_contrasena: str, rol: str,
                  nombre: str | None = None, dni: str | None = None,
                  telefono: str | None = None, cargo: str | None = None) -> Usuario:
    """
    Inserta un usuario nuevo en la base de datos (con sus datos personales opcionales).
    Nota: la contraseña ya llega ENCRIPTADA (el hash lo hace el servicio).
    """
    nuevo = Usuario(correo=correo, hash_contrasena=hash_contrasena, rol=rol,
                    nombre=nombre, dni=dni, telefono=telefono, cargo=cargo)
    db.add(nuevo)                                   # lo prepara para guardar
    asignar_codigo(db, nuevo, prefijo_por_rol(rol))  # codigo legible AD-001 / CO-001
    db.commit()                                     # confirma el cambio en PostgreSQL
    db.refresh(nuevo)                               # recarga el objeto con el id ya asignado
    return nuevo


def actualizar_datos_personales(db: Session, usuario: Usuario, campos: dict) -> Usuario:
    """Actualiza los datos personales (nombre/dni/telefono/cargo) presentes en `campos`.
    Recibe: el usuario y un dict con solo las claves a cambiar."""
    for clave in ("nombre", "dni", "telefono", "cargo"):
        if clave in campos:
            setattr(usuario, clave, campos[clave])
    db.commit()
    db.refresh(usuario)
    return usuario


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
