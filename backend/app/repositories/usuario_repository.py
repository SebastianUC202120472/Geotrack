from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.usuario import Usuario
from app.core.codigos import asignar_codigo, prefijo_por_rol


def listar_personal(db: Session) -> List[Usuario]:
    """Lista usuarios del panel (admin/almacén), excluye conductores. Recibe: sesion db."""
    return (
        db.query(Usuario)
        .filter(Usuario.rol != "conductor")
        .order_by(Usuario.codigo.asc())
        .all()
    )


def actualizar_rol(db: Session, usuario: Usuario, rol: str) -> Usuario:
    """Cambia el rol del usuario. Recibe: usuario y nuevo rol."""
    usuario.rol = rol
    db.commit()
    db.refresh(usuario)
    return usuario


def actualizar_estado(db: Session, usuario: Usuario, estado: bool) -> Usuario:
    """Activa o desactiva un usuario. Recibe: usuario y estado bool."""
    usuario.estado = estado
    db.commit()
    db.refresh(usuario)
    return usuario


def obtener_por_correo(db: Session, correo: str) -> Optional[Usuario]:
    """Busca un usuario por correo. Recibe: correo."""
    return db.query(Usuario).filter(Usuario.correo == correo).first()


def obtener_por_id(db: Session, usuario_id: int) -> Optional[Usuario]:
    """Busca un usuario por id. Recibe: usuario_id."""
    return db.query(Usuario).filter(Usuario.id == usuario_id).first()


def crear_usuario(db: Session, correo: str, hash_contrasena: str, rol: str,
                  nombre: str | None = None, dni: str | None = None,
                  telefono: str | None = None, cargo: str | None = None) -> Usuario:
    """Inserta un usuario nuevo. Recibe: correo, hash ya encriptado, rol y datos personales opcionales."""
    nuevo = Usuario(correo=correo, hash_contrasena=hash_contrasena, rol=rol,
                    nombre=nombre, dni=dni, telefono=telefono, cargo=cargo)
    db.add(nuevo)
    asignar_codigo(db, nuevo, prefijo_por_rol(rol))  # codigo legible AD-001 / CO-001
    db.commit()
    db.refresh(nuevo)
    return nuevo


def actualizar_datos_personales(db: Session, usuario: Usuario, campos: dict) -> Usuario:
    """Actualiza nombre/dni/telefono/cargo del usuario. Recibe: usuario y dict con campos a cambiar."""
    for clave in ("nombre", "dni", "telefono", "cargo"):
        if clave in campos:
            setattr(usuario, clave, campos[clave])
    db.commit()
    db.refresh(usuario)
    return usuario


def actualizar_hash(db: Session, usuario_id: int, hash_contrasena: str) -> Optional[Usuario]:
    """Reemplaza el hash de contrasena del usuario. Recibe: usuario_id y hash ya generado."""
    usuario = obtener_por_id(db, usuario_id)
    if usuario is None:
        return None
    usuario.hash_contrasena = hash_contrasena
    db.commit()
    db.refresh(usuario)
    return usuario
