import os
import time
import glob
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories import conductor_repository, usuario_repository, ubicacion_repository, solicitud_restablecimiento_repository
from app.core.security import get_password_hash
from app.schemas.conductor import ConductorCreate, ConductorUpdate, UbicacionRequest, ConductorResetContrasena


def _a_respuesta(db: Session, usuario, ids_pendientes=None) -> dict:
    """Arma la ficha del conductor cruzando perfil, vehículo y estado de solicitud de clave. Recibe usuario y set opcional de ids pendientes."""
    perfil = conductor_repository.obtener_perfil(db, usuario.id)
    vehiculo = conductor_repository.vehiculo_de(db, usuario.id)
    return {
        "usuario_id": usuario.id,
        "codigo": usuario.codigo,
        "correo": usuario.correo,
        "estado": usuario.estado,
        "en_ruta": conductor_repository.tiene_ruta_activa(db, usuario.id),
        "solicito_restablecimiento": (usuario.id in ids_pendientes) if ids_pendientes is not None else False,
        "nombre": perfil.nombre if perfil else None,
        "telefono": perfil.telefono if perfil else None,
        "dni": perfil.dni if perfil else None,
        "foto_url": perfil.foto_url if perfil else None,
        "vehiculo": vehiculo,
    }


def listar(db: Session) -> list:
    """Lista todos los conductores con su ficha. Recibe: sesion de BD."""
    pendientes = solicitud_restablecimiento_repository.ids_pendientes(db)
    return [_a_respuesta(db, u, pendientes) for u in conductor_repository.listar_usuarios_conductores(db)]


def obtener_uno(db: Session, usuario) -> dict:
    """Devuelve la ficha del conductor autenticado. Recibe: sesion y usuario del token."""
    return _a_respuesta(db, usuario)


def crear(db: Session, datos: ConductorCreate) -> dict:
    """Crea un nuevo conductor (usuario + perfil). Recibe: sesion y datos del schema."""
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


def restablecer_contrasena(db: Session, usuario_id: int, datos: ConductorResetContrasena) -> dict:
    """Fija una nueva contrasena hasheada para un conductor activo. Recibe: id y nueva clave."""
    usuario = _conductor_activo(db, usuario_id)
    usuario_repository.actualizar_hash(db, usuario.id, get_password_hash(datos.contrasena))
    solicitud_restablecimiento_repository.marcar_atendidas(db, usuario.id)
    return {"mensaje": "Contraseña restablecida correctamente"}


def registrar_ubicacion(db: Session, conductor_id: int, datos: UbicacionRequest) -> dict:
    """Guarda (upsert) la última posición del conductor que envía la app móvil."""
    ubicacion_repository.upsert(db, conductor_id, datos.latitud, datos.longitud)
    return {"mensaje": "Ubicación registrada"}


def eliminar(db: Session, usuario_id: int) -> dict:
    """Soft-delete del conductor: lo desactiva y libera su vehiculo. Bloquea si tiene ruta activa."""
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


DIR_FOTOS = os.path.join("uploads", "conductores")
EXTENSIONES_IMAGEN = {".jpg", ".jpeg", ".png", ".webp"}


def guardar_foto(db: Session, usuario_id: int, contenido: bytes, nombre_archivo: str) -> dict:
    """Guarda o reemplaza la foto de un conductor activo. Recibe: id, bytes y nombre original del archivo."""
    usuario = _conductor_activo(db, usuario_id)

    _, extension = os.path.splitext((nombre_archivo or "").lower())
    if extension not in EXTENSIONES_IMAGEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato no permitido. Usa: {', '.join(sorted(EXTENSIONES_IMAGEN))}",
        )

    os.makedirs(DIR_FOTOS, exist_ok=True)
    for viejo in glob.glob(os.path.join(DIR_FOTOS, f"cond_{usuario_id}.*")):
        try:
            os.remove(viejo)
        except OSError:
            pass

    nombre_final = f"cond_{usuario_id}{extension}"
    ruta_fisica = os.path.join(DIR_FOTOS, nombre_final)
    with open(ruta_fisica, "wb") as f:
        f.write(contenido)

    # ?v= invalida la cache del navegador al reemplazar la foto.
    url = f"/media/conductores/{nombre_final}?v={int(time.time())}"
    conductor_repository.actualizar_foto(db, usuario_id, url)
    return _a_respuesta(db, usuario)
