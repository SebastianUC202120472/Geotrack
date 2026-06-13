# app/services/conductor_service.py
# - Lista los conductores con su ficha (nombre/teléfono/DNI) y el vehículo que tienen asignado.
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories import conductor_repository, usuario_repository
from app.core.security import get_password_hash
from app.schemas.conductor import ConductorCreate


def _a_respuesta(db: Session, usuario) -> dict:
    """Arma la ficha del conductor cruzando perfil + vehículo asignado."""
    perfil = conductor_repository.obtener_perfil(db, usuario.id)
    vehiculo = conductor_repository.vehiculo_de(db, usuario.id)
    return {
        "usuario_id": usuario.id,
        "codigo": usuario.codigo,
        "correo": usuario.correo,
        "estado": usuario.estado,
        "nombre": perfil.nombre if perfil else None,
        "telefono": perfil.telefono if perfil else None,
        "dni": perfil.dni if perfil else None,
        "vehiculo": vehiculo,
    }


def listar(db: Session) -> list:
    return [_a_respuesta(db, u) for u in conductor_repository.listar_usuarios_conductores(db)]


# Ficha del propio conductor (su perfil). Recibe: el Usuario del token.
def obtener_uno(db: Session, usuario) -> dict:
    return _a_respuesta(db, usuario)


def crear(db: Session, datos: ConductorCreate) -> dict:
    if usuario_repository.obtener_por_correo(db, datos.correo):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El correo ya está registrado")

    usuario = usuario_repository.crear_usuario(
        db, correo=datos.correo, hash_contrasena=get_password_hash(datos.contrasena), rol="conductor"
    )
    conductor_repository.crear_perfil(
        db, usuario_id=usuario.id, nombre=datos.nombre, telefono=datos.telefono, dni=datos.dni
    )
    return _a_respuesta(db, usuario)
