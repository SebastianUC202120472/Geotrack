from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.usuario import Usuario
from app.models.conductor import PerfilConductor
from app.models.vehiculo import Vehiculo
from app.models.ruta import Ruta


def listar_usuarios_conductores(db: Session) -> List[Usuario]:
    # Retorna conductores activos. Recibe: sesion de BD.
    return (
        db.query(Usuario)
        .filter(Usuario.rol == "conductor", Usuario.estado.is_(True))
        .order_by(Usuario.codigo.asc())
        .all()
    )


def obtener_perfil(db: Session, usuario_id: int) -> Optional[PerfilConductor]:
    return db.query(PerfilConductor).filter(PerfilConductor.usuario_id == usuario_id).first()


def vehiculo_de(db: Session, usuario_id: int) -> Optional[Vehiculo]:
    """Retorna el vehiculo asignado al conductor. Recibe: usuario_id."""
    return db.query(Vehiculo).filter(Vehiculo.conductor_id == usuario_id).first()


def crear_perfil(db: Session, usuario_id: int, nombre: str, telefono=None, dni=None) -> PerfilConductor:
    perfil = PerfilConductor(usuario_id=usuario_id, nombre=nombre, telefono=telefono, dni=dni)
    db.add(perfil)
    db.commit()
    db.refresh(perfil)
    return perfil


def actualizar_perfil(db: Session, usuario_id: int, nombre=None, telefono=None, dni=None) -> Optional[PerfilConductor]:
    """Actualiza nombre, telefono y DNI del perfil. Recibe: usuario_id y campos opcionales."""
    perfil = obtener_perfil(db, usuario_id)
    if perfil is None:
        return None
    if nombre is not None:
        perfil.nombre = nombre
    perfil.telefono = telefono
    perfil.dni = dni
    db.commit()
    db.refresh(perfil)
    return perfil


def tiene_ruta_activa(db: Session, usuario_id: int) -> bool:
    """Indica si el conductor tiene ruta activa (CREADA o EN_PROGRESO). Recibe: usuario_id."""
    return (
        db.query(Ruta)
        .filter(Ruta.conductor_id == usuario_id, Ruta.estado.in_(["CREADA", "EN_PROGRESO"]))
        .first()
        is not None
    )


def desasignar_vehiculo(db: Session, usuario_id: int) -> None:
    """Desvincula el vehiculo del conductor. Recibe: usuario_id."""
    vehiculo = db.query(Vehiculo).filter(Vehiculo.conductor_id == usuario_id).first()
    if vehiculo:
        vehiculo.conductor_id = None
        db.commit()


def actualizar_foto(db: Session, usuario_id: int, foto_url: str) -> Optional[PerfilConductor]:
    """Actualiza la foto de perfil del conductor. Recibe: usuario_id y foto_url."""
    perfil = obtener_perfil(db, usuario_id)
    if perfil is None:
        return None
    perfil.foto_url = foto_url
    db.commit()
    db.refresh(perfil)
    return perfil
