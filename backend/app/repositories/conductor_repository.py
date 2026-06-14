# app/repositories/conductor_repository.py
# Lee/escribe el perfil del conductor y arma la lista de conductores cruzando usuarios (rol conductor) + perfil + vehículo asignado. La USA.
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.usuario import Usuario
from app.models.conductor import PerfilConductor
from app.models.vehiculo import Vehiculo
from app.models.ruta import Ruta


def listar_usuarios_conductores(db: Session) -> List[Usuario]:
    # Solo conductores ACTIVOS (los eliminados quedan con estado=False y se ocultan).
    return (
        db.query(Usuario)
        .filter(Usuario.rol == "conductor", Usuario.estado.is_(True))
        .order_by(Usuario.codigo.asc())
        .all()
    )


def obtener_perfil(db: Session, usuario_id: int) -> Optional[PerfilConductor]:
    return db.query(PerfilConductor).filter(PerfilConductor.usuario_id == usuario_id).first()


def vehiculo_de(db: Session, usuario_id: int) -> Optional[Vehiculo]:
    """Vehículo asignado a ese conductor (si tiene)."""
    return db.query(Vehiculo).filter(Vehiculo.conductor_id == usuario_id).first()


def crear_perfil(db: Session, usuario_id: int, nombre: str, telefono=None, dni=None) -> PerfilConductor:
    perfil = PerfilConductor(usuario_id=usuario_id, nombre=nombre, telefono=telefono, dni=dni)
    db.add(perfil)
    db.commit()
    db.refresh(perfil)
    return perfil


def actualizar_perfil(db: Session, usuario_id: int, nombre=None, telefono=None, dni=None) -> Optional[PerfilConductor]:
    """Actualiza la ficha del conductor. `nombre` se cambia solo si llega; teléfono
    y DNI se reemplazan por el valor recibido (None los deja vacíos)."""
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
    """True si el conductor tiene una ruta sin cerrar (CREADA o EN_PROGRESO)."""
    return (
        db.query(Ruta)
        .filter(Ruta.conductor_id == usuario_id, Ruta.estado.in_(["CREADA", "EN_PROGRESO"]))
        .first()
        is not None
    )


def desasignar_vehiculo(db: Session, usuario_id: int) -> None:
    """Libera el vehículo que tuviera asignado ese conductor (conductor_id = None)."""
    vehiculo = db.query(Vehiculo).filter(Vehiculo.conductor_id == usuario_id).first()
    if vehiculo:
        vehiculo.conductor_id = None
        db.commit()
