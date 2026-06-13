# app/repositories/conductor_repository.py
# ============================================================================
# CAPA: REPOSITORIO (acceso a datos) — Conductores
# ----------------------------------------------------------------------------
# Lee/escribe el perfil del conductor y arma la lista de conductores cruzando
# usuarios (rol conductor) + perfil + vehículo asignado.
# La USA: services/conductor_service.py.
# ============================================================================
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.usuario import Usuario
from app.models.conductor import PerfilConductor
from app.models.vehiculo import Vehiculo


def listar_usuarios_conductores(db: Session) -> List[Usuario]:
    return (
        db.query(Usuario)
        .filter(Usuario.rol == "conductor")
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
