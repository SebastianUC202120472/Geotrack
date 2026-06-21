# app/services/vehiculo_service.py
# Listar y registrar vehículos (evitando placas duplicadas).
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories import vehiculo_repository, conductor_repository, usuario_repository
from app.schemas.vehiculo import VehiculoCreate, VehiculoUpdate


def listar_vehiculos(db: Session):
    """Devuelve los vehículos activos. El estado se recalcula: si el conductor del
    vehículo tiene una ruta activa, el vehículo aparece EN_RUTA (no DISPONIBLE)."""
    vehiculos = vehiculo_repository.listar(db)
    salida = []
    for v in vehiculos:
        estado = v.estado
        if v.conductor_id and conductor_repository.tiene_ruta_activa(db, v.conductor_id):
            estado = "EN_RUTA"
        salida.append({
            "id": v.id,
            "codigo": v.codigo,
            "placa": v.placa,
            "marca": v.marca,
            "capacidad_volumetrica": v.capacidad_volumetrica,
            "capacidad_cajas": v.capacidad_cajas,
            "estado": estado,
            "conductor_id": v.conductor_id,
        })
    return salida


def crear_vehiculo(db: Session, datos: VehiculoCreate):
    """Registra un vehículo; rechaza si la placa ya existe."""
    if vehiculo_repository.obtener_por_placa(db, datos.placa):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un vehículo con esa placa",
        )
    vehiculo = vehiculo_repository.crear(
        db,
        placa=datos.placa,
        marca=datos.marca,
        capacidad_volumetrica=datos.capacidad_volumetrica,
        capacidad_cajas=datos.capacidad_cajas,
        estado=datos.estado,
        conductor_id=datos.conductor_id,
    )
    db.commit()
    db.refresh(vehiculo)
    return vehiculo


def _a_dict(vehiculo) -> dict:
    """Arma la respuesta de un vehículo (mismos campos que VehiculoResponse)."""
    return {
        "id": vehiculo.id,
        "codigo": vehiculo.codigo,
        "placa": vehiculo.placa,
        "marca": vehiculo.marca,
        "capacidad_volumetrica": vehiculo.capacidad_volumetrica,
        "capacidad_cajas": vehiculo.capacidad_cajas,
        "estado": vehiculo.estado,
        "conductor_id": vehiculo.conductor_id,
    }


def actualizar_vehiculo(db: Session, vehiculo_id: int, datos: VehiculoUpdate):
    """CUS-08/09: edita un vehículo (marca/capacidades) y/o (re)asigna su conductor.
    Recibe: id del vehículo y los campos a cambiar (solo se aplican los enviados).
    Si llega conductor_id no nulo, valida que sea un conductor activo y mantiene la
    relación 1-a-1 (libera el vehículo previo del conductor)."""
    vehiculo = vehiculo_repository.obtener_por_id(db, vehiculo_id)
    if vehiculo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehículo no encontrado")

    campos = datos.model_dump(exclude_unset=True)  # solo lo que el cliente envió

    # Datos simples del vehículo.
    for campo in ("marca", "capacidad_volumetrica", "capacidad_cajas"):
        if campo in campos:
            setattr(vehiculo, campo, campos[campo])

    # Reasignación de conductor (si se envió conductor_id, aunque sea null = desvincular).
    if "conductor_id" in campos:
        conductor_id = campos["conductor_id"]
        if conductor_id is not None:
            conductor = usuario_repository.obtener_por_id(db, conductor_id)
            if conductor is None or conductor.rol != "conductor" or not conductor.estado:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El conductor indicado no existe o no está activo",
                )
        # reasignar_conductor confirma TODOS los cambios pendientes del vehículo.
        vehiculo_repository.reasignar_conductor(db, vehiculo, conductor_id)
    else:
        db.commit()
        db.refresh(vehiculo)

    return _a_dict(vehiculo)


def eliminar_vehiculo(db: Session, vehiculo_id: int) -> dict:
    """CUS-08: da de baja (lógica) un vehículo y libera a su conductor. Recibe: id."""
    vehiculo = vehiculo_repository.obtener_por_id(db, vehiculo_id)
    if vehiculo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehículo no encontrado")
    vehiculo_repository.eliminar(db, vehiculo)
    return {"mensaje": "Vehículo eliminado"}
