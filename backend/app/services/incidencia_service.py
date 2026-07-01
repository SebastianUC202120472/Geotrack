import os
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories import incidencia_repository, ruta_repository, usuario_repository
from app.models.conductor import PerfilConductor
from app.services import notificaciones_service

DIR_INCIDENCIAS = os.path.join("uploads", "incidencias")
EXTENSIONES_IMAGEN = {".jpg", ".jpeg", ".png", ".webp"}


def _nombre_conductor(db: Session, conductor_id: int):
    """Devuelve el nombre del conductor o su correo. Recibe conductor_id."""
    perfil = db.query(PerfilConductor).filter(PerfilConductor.usuario_id == conductor_id).first()
    if perfil and perfil.nombre:
        return perfil.nombre
    u = usuario_repository.obtener_por_id(db, conductor_id)
    return u.correo if u else None


def _a_respuesta(db: Session, inc) -> dict:
    """Serializa una incidencia con nombres legibles. Recibe la instancia de incidencia."""
    ruta = ruta_repository.obtener_ruta_por_id(db, inc.ruta_id)
    return {
        "id": inc.id,
        "codigo": inc.codigo,
        "ruta_id": inc.ruta_id,
        "ruta_nombre": ruta.nombre if ruta else None,
        "conductor_id": inc.conductor_id,
        "conductor_nombre": _nombre_conductor(db, inc.conductor_id),
        "vehiculo_placa": inc.vehiculo_placa,
        "tipo": inc.tipo,
        "descripcion": inc.descripcion,
        "url_evidencia": inc.url_evidencia,
        "latitud": inc.latitud,
        "longitud": inc.longitud,
        "estado": inc.estado,
        "creado_en": inc.creado_en,
        "resuelto_en": inc.resuelto_en,
        "nota_resolucion": inc.nota_resolucion,
        "puede_solucionar_solo": bool(inc.puede_solucionar_solo),
        "ayuda_enviada_en": inc.ayuda_enviada_en,
        "ayuda_detalle": inc.ayuda_detalle,
    }


def reportar(db: Session, conductor_id: int, datos) -> dict:
    """Registra un auxilio mecánico pausando la ruta activa. Recibe conductor_id y IncidenciaCreate."""
    ruta = ruta_repository.obtener_ruta_activa_por_conductor(db, conductor_id)
    if not ruta:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No tienes una ruta activa para reportar un auxilio")

    abierta = incidencia_repository.obtener_abierta_por_ruta(db, ruta.id)
    if abierta:
        return _a_respuesta(db, abierta)  # ya está pausada: evitamos duplicar

    inc = incidencia_repository.crear(
        db,
        ruta_id=ruta.id,
        conductor_id=conductor_id,
        vehiculo_placa=ruta.vehiculo_placa,
        tipo=(datos.tipo or "AVERIA_MECANICA"),
        descripcion=(datos.descripcion or None),
        latitud=datos.latitud,
        longitud=datos.longitud,
        puede_solucionar_solo=bool(getattr(datos, "puede_solucionar_solo", False)),
    )
    try:
        nombre = _nombre_conductor(db, conductor_id)
        solo = " (puede solucionarlo solo)" if inc.puede_solucionar_solo else ""
        notificaciones_service.registrar(
            db, "incidencias", "Auxilio mecánico solicitado",
            f"{nombre or 'Conductor'} — ruta {ruta.nombre or ruta.codigo}{solo}", "/auxilio?estado=ABIERTA", inc.id)
    except Exception:
        pass
    return _a_respuesta(db, inc)


def guardar_evidencia(db: Session, incidencia_id: int, conductor_id: int, contenido: bytes, nombre_archivo: str) -> dict:
    """Guarda la foto de averia y la asocia a la incidencia. Recibe id, conductor_id, bytes e imagen."""
    inc = incidencia_repository.obtener(db, incidencia_id)
    if not inc or inc.conductor_id != conductor_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incidencia no encontrada")

    _, extension = os.path.splitext(nombre_archivo.lower())
    if extension not in EXTENSIONES_IMAGEN:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Formato no permitido. Usa: {', '.join(sorted(EXTENSIONES_IMAGEN))}")

    os.makedirs(DIR_INCIDENCIAS, exist_ok=True)
    nombre_final = f"inc_{inc.id}{extension}"
    with open(os.path.join(DIR_INCIDENCIAS, nombre_final), "wb") as f:
        f.write(contenido)
    inc.url_evidencia = f"/media/incidencias/{nombre_final}"
    incidencia_repository.guardar(db)
    return _a_respuesta(db, inc)


def _cerrar(db: Session, incidencia_id: int, usuario_id: int, nota, por_defecto: str) -> dict:
    """Marca la incidencia como RESUELTA. Recibe id, usuario, nota y texto por defecto."""
    inc = incidencia_repository.obtener(db, incidencia_id)
    if not inc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incidencia no encontrada")
    if inc.estado == "RESUELTA":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La incidencia ya estaba resuelta")
    inc.estado = "RESUELTA"
    inc.resuelto_en = datetime.utcnow()
    inc.resuelto_por = usuario_id
    inc.nota_resolucion = (nota or por_defecto)
    incidencia_repository.guardar(db)
    return _a_respuesta(db, inc)


def reanudar(db: Session, incidencia_id: int, usuario_id: int, nota=None) -> dict:
    """El conductor reanuda su ruta cerrando la incidencia abierta. Recibe id, conductor_id y nota."""
    inc = incidencia_repository.obtener(db, incidencia_id)
    if not inc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incidencia no encontrada")
    if inc.conductor_id != usuario_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Esta incidencia no es de tu ruta")
    return _cerrar(db, incidencia_id, usuario_id, nota, "Reanudada por el conductor")


def mandar_ayuda(db: Session, incidencia_id: int, admin_id: int, tipo: str, nota=None) -> dict:
    """Registra el envio de ayuda al conductor sin resolver la incidencia. Recibe id, admin_id, tipo y nota."""
    inc = incidencia_repository.obtener(db, incidencia_id)
    if not inc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incidencia no encontrada")
    if inc.estado == "RESUELTA":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La incidencia ya fue resuelta")
    if inc.puede_solucionar_solo:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="El conductor indicó que puede solucionarlo solo; no procede mandar ayuda.")
    if not (tipo or "").strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Indica el tipo de ayuda a enviar")
    detalle = tipo.strip() + (f": {nota.strip()}" if (nota and nota.strip()) else "")
    inc.ayuda_enviada_en = datetime.utcnow()
    inc.ayuda_enviada_por = admin_id
    inc.ayuda_detalle = detalle[:255]
    incidencia_repository.guardar(db)
    return _a_respuesta(db, inc)


def listar(db: Session, estado=None) -> list:
    """Lista las incidencias con filtro opcional por estado."""
    return [_a_respuesta(db, i) for i in incidencia_repository.listar(db, estado)]


def contar_abiertas(db: Session) -> int:
    """Cuenta las incidencias con estado ABIERTA."""
    return incidencia_repository.contar_abiertas(db)
