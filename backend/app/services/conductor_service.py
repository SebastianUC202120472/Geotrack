# app/services/conductor_service.py
# - Lista los conductores con su ficha (nombre/teléfono/DNI) y el vehículo que tienen asignado.
import os
import time
import glob
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories import conductor_repository, usuario_repository, ubicacion_repository
from app.core.security import get_password_hash
from app.schemas.conductor import ConductorCreate, ConductorUpdate, UbicacionRequest


def _a_respuesta(db: Session, usuario) -> dict:
    """Arma la ficha del conductor cruzando perfil + vehículo asignado."""
    perfil = conductor_repository.obtener_perfil(db, usuario.id)
    vehiculo = conductor_repository.vehiculo_de(db, usuario.id)
    return {
        "usuario_id": usuario.id,
        "codigo": usuario.codigo,
        "correo": usuario.correo,
        "estado": usuario.estado,
        # En ruta = tiene una ruta sin cerrar (CREADA/EN_PROGRESO). El panel lo muestra
        # como "En ruta" en vez de "Disponible" hasta que cierre el día.
        "en_ruta": conductor_repository.tiene_ruta_activa(db, usuario.id),
        "nombre": perfil.nombre if perfil else None,
        "telefono": perfil.telefono if perfil else None,
        "dni": perfil.dni if perfil else None,
        "foto_url": perfil.foto_url if perfil else None,
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


def _conductor_activo(db: Session, usuario_id: int):
    """Devuelve el usuario si es un conductor activo; si no, lanza 404."""
    usuario = usuario_repository.obtener_por_id(db, usuario_id)
    if usuario is None or usuario.rol != "conductor" or not usuario.estado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conductor no encontrado")
    return usuario


def actualizar(db: Session, usuario_id: int, datos: ConductorUpdate) -> dict:
    """Edita la ficha (nombre/teléfono/DNI) de un conductor activo."""
    usuario = _conductor_activo(db, usuario_id)
    conductor_repository.actualizar_perfil(
        db, usuario_id, nombre=datos.nombre, telefono=datos.telefono, dni=datos.dni
    )
    return _a_respuesta(db, usuario)


def registrar_ubicacion(db: Session, conductor_id: int, datos: UbicacionRequest) -> dict:
    """Guarda (upsert) la última posición del conductor que envía la app móvil."""
    ubicacion_repository.upsert(db, conductor_id, datos.latitud, datos.longitud)
    return {"mensaje": "Ubicación registrada"}


def eliminar(db: Session, usuario_id: int) -> dict:
    """Soft-delete: desactiva al conductor (preserva su historial). Bloquea si
    tiene una ruta activa y libera su vehículo."""
    usuario = _conductor_activo(db, usuario_id)
    if conductor_repository.tiene_ruta_activa(db, usuario_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede eliminar: el conductor tiene una ruta activa",
        )
    conductor_repository.desasignar_vehiculo(db, usuario_id)
    usuario.estado = False
    db.commit()
    return {"mensaje": "Conductor eliminado"}


# Carpeta de fotos de conductores (servida en /media). Mismos formatos que el POD.
DIR_FOTOS = os.path.join("uploads", "conductores")
EXTENSIONES_IMAGEN = {".jpg", ".jpeg", ".png", ".webp"}


def guardar_foto(db: Session, usuario_id: int, contenido: bytes, nombre_archivo: str) -> dict:
    """Guarda/reemplaza la foto de un conductor activo. Recibe: id, bytes y nombre
    original del archivo. Devuelve: la ficha del conductor con la nueva foto_url."""
    usuario = _conductor_activo(db, usuario_id)

    _, extension = os.path.splitext((nombre_archivo or "").lower())
    if extension not in EXTENSIONES_IMAGEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato no permitido. Usa: {', '.join(sorted(EXTENSIONES_IMAGEN))}",
        )

    os.makedirs(DIR_FOTOS, exist_ok=True)
    # Borra cualquier foto previa del conductor (evita huérfanos al cambiar de formato).
    for viejo in glob.glob(os.path.join(DIR_FOTOS, f"cond_{usuario_id}.*")):
        try:
            os.remove(viejo)
        except OSError:
            pass

    nombre_final = f"cond_{usuario_id}{extension}"
    ruta_fisica = os.path.join(DIR_FOTOS, nombre_final)
    with open(ruta_fisica, "wb") as f:
        f.write(contenido)

    # Query ?v= para invalidar la caché del navegador/expo-image al reemplazar.
    url = f"/media/conductores/{nombre_final}?v={int(time.time())}"
    conductor_repository.actualizar_foto(db, usuario_id, url)
    return _a_respuesta(db, usuario)
