import os
import time
import glob
import secrets
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.imagenes import validar_imagen
from app.repositories import conductor_repository, usuario_repository, ubicacion_repository, solicitud_restablecimiento_repository, vehiculo_repository
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
        "licencia_numero": perfil.licencia_numero if perfil else None,
        "licencia_vencimiento": perfil.licencia_vencimiento if perfil else None,
        "vehiculo": vehiculo,
    }


def listar(db: Session) -> list:
    """Lista todos los conductores con su ficha. Recibe: sesion de BD."""
    pendientes = solicitud_restablecimiento_repository.ids_pendientes(db)
    return [_a_respuesta(db, u, pendientes) for u in conductor_repository.listar_usuarios_conductores(db)]


def obtener_uno(db: Session, usuario) -> dict:
    """Devuelve la ficha del conductor autenticado. Recibe: sesion y usuario del token."""
    return _a_respuesta(db, usuario)


def _vehiculo_libre_o_400(db: Session, vehiculo_id: int):
    """Devuelve el vehiculo si existe y no tiene conductor; si no, lanza 400. Recibe el vehiculo_id."""
    vehiculo = vehiculo_repository.obtener_por_id(db, vehiculo_id)
    if vehiculo is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El vehículo elegido no existe o fue dado de baja")
    if vehiculo.conductor_id is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"El vehículo {vehiculo.placa} ya está asignado a otro conductor")
    return vehiculo


def crear(db: Session, datos: ConductorCreate) -> dict:
    """Crea un nuevo conductor (usuario + perfil con licencia) y, si se eligio, le asigna su vehiculo. Recibe: sesion y datos del schema."""
    if usuario_repository.obtener_por_correo(db, datos.correo):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El correo ya está registrado")
    # Se valida el vehiculo ANTES de crear la cuenta para no dejar un alta a medias.
    vehiculo = _vehiculo_libre_o_400(db, datos.vehiculo_id) if datos.vehiculo_id else None

    usuario = usuario_repository.crear_usuario(
        db, correo=datos.correo, hash_contrasena=get_password_hash(datos.contrasena), rol="conductor"
    )
    conductor_repository.crear_perfil(
        db, usuario_id=usuario.id, nombre=datos.nombre, telefono=datos.telefono, dni=datos.dni,
        licencia_numero=datos.licencia_numero, licencia_vencimiento=datos.licencia_vencimiento,
    )
    if vehiculo is not None:
        vehiculo_repository.reasignar_conductor(db, vehiculo, usuario.id)
    return _a_respuesta(db, usuario)


def _conductor_activo(db: Session, usuario_id: int):
    """Devuelve el usuario si es un conductor activo; si no, lanza 404."""
    usuario = usuario_repository.obtener_por_id(db, usuario_id)
    if usuario is None or usuario.rol != "conductor" or not usuario.estado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conductor no encontrado")
    return usuario


def actualizar(db: Session, usuario_id: int, datos: ConductorUpdate) -> dict:
    """Edita la ficha (correo/nombre/teléfono/DNI/licencia) de un conductor activo. Recibe id y cambios."""
    usuario = _conductor_activo(db, usuario_id)
    if datos.correo:
        nuevo_correo = str(datos.correo).strip().lower()
        if nuevo_correo != usuario.correo:
            existente = usuario_repository.obtener_por_correo(db, nuevo_correo)
            if existente and existente.id != usuario.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El correo ya está registrado por otra cuenta",
                )
            usuario_repository.actualizar_correo(db, usuario, nuevo_correo)
    # La licencia solo se toca si viene en la peticion (asi un cliente viejo no la borra).
    licencia = datos.model_dump(include={"licencia_numero", "licencia_vencimiento"}, exclude_unset=True)
    conductor_repository.actualizar_perfil(
        db, usuario_id, nombre=datos.nombre, telefono=datos.telefono, dni=datos.dni, licencia=licencia
    )
    return _a_respuesta(db, usuario)


def validar_para_ruta(db: Session, conductor_id: int):
    """Comprueba que el conductor pueda recibir una ruta: activo, con vehiculo vinculado y sin la
    licencia vencida (C12-01, C19-01). Recibe el id. Devuelve (usuario, vehiculo) o lanza 400."""
    from app.core.fechas import hoy_local  # import local: fechas depende de config

    usuario = usuario_repository.obtener_por_id(db, conductor_id)
    if usuario is None or usuario.rol != "conductor" or not usuario.estado:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El conductor elegido no existe o está dado de baja")
    vehiculo = vehiculo_repository.obtener_por_conductor(db, conductor_id)
    if vehiculo is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El conductor no tiene un vehículo asignado. Asígnale uno en Flota de Vehículos.",
        )
    perfil = conductor_repository.obtener_perfil(db, conductor_id)
    if perfil and perfil.licencia_vencimiento and perfil.licencia_vencimiento < hoy_local():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La licencia de conducir del conductor está vencida. Actualiza su ficha antes de asignarle rutas.",
        )
    return usuario, vehiculo


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


def guardar_foto(db: Session, usuario_id: int, contenido: bytes, nombre_archivo: str) -> dict:
    """Guarda o reemplaza la foto de un conductor activo. Recibe: id, bytes y nombre original del archivo."""
    usuario = _conductor_activo(db, usuario_id)

    # La extension sale del contenido real, no del nombre que manda el cliente.
    extension = validar_imagen(contenido)

    os.makedirs(DIR_FOTOS, exist_ok=True)
    # Borra la foto anterior: el patron viejo (cond_ID.ext, sin sufijo) y el nuevo
    # (cond_ID_<aleatorio>.ext), para no dejar huerfanos al cambiar de esquema.
    for patron in (f"cond_{usuario_id}.*", f"cond_{usuario_id}_*"):
        for viejo in glob.glob(os.path.join(DIR_FOTOS, patron)):
            try:
                os.remove(viejo)
            except OSError:
                pass

    # Sufijo aleatorio: /media es estatico y la foto personal no debe ser adivinable.
    nombre_final = f"cond_{usuario_id}_{secrets.token_hex(8)}{extension}"
    ruta_fisica = os.path.join(DIR_FOTOS, nombre_final)
    with open(ruta_fisica, "wb") as f:
        f.write(contenido)

    # ?v= invalida la cache del navegador al reemplazar la foto.
    url = f"/media/conductores/{nombre_final}?v={int(time.time())}"
    conductor_repository.actualizar_foto(db, usuario_id, url)
    return _a_respuesta(db, usuario)
