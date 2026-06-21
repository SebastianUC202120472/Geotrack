# app/services/recojo_service.py
# Lógica del módulo Inbound de recojos: alta de solicitudes (CUS-10), asignación de
# ruta de recojo (CUS-11) y recepción condicionada en origen (CUS-12).
import os
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.solicitud_recojo import SolicitudRecojo
from app.models.cliente import ClienteCorporativo
from app.models.ruta import Ruta
from app.repositories import recojo_repository, ruta_repository, incidencia_repository
from app.services.geocoder import obtener_coordenadas
from app.services.router import optimizar_secuencia_pedidos, distancia_total
from app.schemas.recojo import (
    SolicitudRecojoCreate,
    SolicitudRecojoUpdate,
    AsignarRutaRecojoRequest,
    AsignarRutaRecojoResponse,
    ManifiestoRecojoResponse,
    ParadaRecojo,
    RecepcionResponse,
)
from app.schemas.ruta import OptimizacionRequest, CierreRutaResponse

# Carpeta donde se guardan las fotos de las Guías de Remisión (servidas en /media/guias).
DIR_GUIAS = os.path.join("uploads", "guias")
EXTENSIONES_IMAGEN = {".jpg", ".jpeg", ".png", ".webp"}


def _distrito_de(direccion: str) -> str:
    """Deriva el distrito del texto de la dirección (igual que pedidos, CUS-16):
    toma lo que va tras la primera coma. Recibe: la dirección de origen."""
    partes = (direccion or "").split(",")
    return partes[1].strip() if len(partes) >= 2 else "ZONA_DESCONOCIDA"


# === CUS-10: alta de solicitud de recojo (admin) ===
def crear_solicitud(db: Session, datos: SolicitudRecojoCreate, usuario_id: int | None = None) -> SolicitudRecojo:
    """Crea una solicitud de recojo: valida el cliente, geocodifica el origen y la deja
    en SOLICITADO. Recibe: los datos del formulario (CUS-10)."""
    cliente = db.query(ClienteCorporativo).filter(ClienteCorporativo.id == datos.cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=400, detail="El cliente indicado no existe")

    direccion = (datos.direccion_origen or "").strip()
    if not direccion:
        raise HTTPException(status_code=400, detail="La dirección de origen es obligatoria")
    if datos.volumen_estimado_m3 is not None and datos.volumen_estimado_m3 < 0:
        raise HTTPException(status_code=400, detail="El volumen estimado no puede ser negativo")

    lat, lng = obtener_coordenadas(direccion)
    recojo = SolicitudRecojo(
        cliente_id=cliente.id,
        cliente_origen=cliente.razon_social,
        direccion_origen=direccion,
        distrito=_distrito_de(direccion) if (lat and lng) else None,
        latitud=lat,
        longitud=lng,
        volumen_estimado_m3=datos.volumen_estimado_m3,
        contacto_origen=datos.contacto_origen,
        referencia=datos.referencia,
        conversacion_id=datos.conversacion_id,
        estado="SOLICITADO",
    )
    recojo_repository.agregar(db, recojo)
    recojo_repository.guardar_cambios(db)
    db.refresh(recojo)
    return recojo


def listar_solicitudes(db: Session, estado: str | None = None):
    """Lista las solicitudes de recojo (filtro opcional por estado)."""
    return recojo_repository.listar(db, estado)


def obtener_solicitud(db: Session, recojo_id: int) -> SolicitudRecojo:
    """Devuelve una solicitud por id, o 404 si no existe. Recibe: id del recojo."""
    recojo = recojo_repository.obtener_por_id(db, recojo_id)
    if not recojo:
        raise HTTPException(status_code=404, detail="Solicitud de recojo no encontrada")
    return recojo


def editar_solicitud(db: Session, recojo_id: int, datos: SolicitudRecojoUpdate) -> SolicitudRecojo:
    """Edita una solicitud mientras está SOLICITADO; re-geocodifica si cambió la dirección.
    Recibe: id del recojo y los campos a actualizar."""
    recojo = obtener_solicitud(db, recojo_id)
    if recojo.estado != "SOLICITADO":
        raise HTTPException(status_code=400, detail="Solo se puede editar una solicitud en estado SOLICITADO")

    if datos.direccion_origen is not None:
        direccion = datos.direccion_origen.strip()
        if not direccion:
            raise HTTPException(status_code=400, detail="La dirección de origen es obligatoria")
        recojo.direccion_origen = direccion
        lat, lng = obtener_coordenadas(direccion)
        recojo.latitud = lat
        recojo.longitud = lng
        recojo.distrito = _distrito_de(direccion) if (lat and lng) else None
    if datos.volumen_estimado_m3 is not None:
        if datos.volumen_estimado_m3 < 0:
            raise HTTPException(status_code=400, detail="El volumen estimado no puede ser negativo")
        recojo.volumen_estimado_m3 = datos.volumen_estimado_m3
    if datos.contacto_origen is not None:
        recojo.contacto_origen = datos.contacto_origen
    if datos.referencia is not None:
        recojo.referencia = datos.referencia

    recojo_repository.guardar_cambios(db)
    db.refresh(recojo)
    return recojo


# === CUS-11: asignar una ruta de recojo (admin) ===
def asignar_ruta_recojo(db: Session, datos: AsignarRutaRecojoRequest, usuario_id: int | None = None) -> AsignarRutaRecojoResponse:
    """Crea una ruta de recojo (tipo=RECOJO) con conductor + vehículo y le cuelga las
    solicitudes seleccionadas. Valida que estén SOLICITADO y que el conductor esté libre.
    Recibe: recojo_ids, conductor_id, vehiculo_placa y nombre opcional (CUS-11)."""
    if not datos.recojo_ids:
        raise HTTPException(status_code=400, detail="Selecciona al menos una solicitud de recojo")

    recojos = recojo_repository.obtener_por_ids(db, datos.recojo_ids)
    if len(recojos) != len(set(datos.recojo_ids)):
        raise HTTPException(status_code=400, detail="Alguna solicitud seleccionada no existe")
    no_disponibles = [r.codigo or r.id for r in recojos if r.estado != "SOLICITADO"]
    if no_disponibles:
        raise HTTPException(status_code=400, detail=f"Estas solicitudes ya no están disponibles: {no_disponibles}")

    activa = ruta_repository.obtener_ruta_activa_por_conductor(db, datos.conductor_id)
    if activa:
        raise HTTPException(
            status_code=400,
            detail=f"El conductor ya tiene una ruta activa ('{activa.nombre}'). Debe cerrarla antes de asignar otra.",
        )

    # Nombre por defecto: "Recojo <distrito del primer recojo con distrito>".
    distrito = next((r.distrito for r in recojos if r.distrito), None)
    nombre = (datos.nombre_ruta or "").strip() or f"Recojo {distrito or 'sin zona'}"

    ruta = ruta_repository.crear_ruta(db, nombre=nombre, conductor_id=datos.conductor_id)
    ruta.tipo = "RECOJO"
    ruta.vehiculo_placa = datos.vehiculo_placa

    for recojo in recojos:
        recojo.ruta_id = ruta.id
        recojo.secuencia = 0
        recojo.estado = "ASIGNADO"

    ruta_repository.guardar_cambios(db)
    return AsignarRutaRecojoResponse(
        mensaje=f"{len(recojos)} recojo(s) asignados a la ruta '{nombre}'",
        ruta_id=ruta.id,
        codigo=ruta.codigo,
    )
