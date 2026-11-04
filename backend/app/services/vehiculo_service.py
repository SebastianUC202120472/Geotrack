from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories import vehiculo_repository, conductor_repository, usuario_repository
from app.schemas.vehiculo import VehiculoCreate, VehiculoUpdate


def listar_vehiculos(db: Session):
    """Devuelve los vehículos activos; recalcula estado a EN_RUTA si el conductor tiene ruta activa."""
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


def validar_conductor_activo(db: Session, conductor_id: int):
    """Comprueba que el id sea de un conductor activo; si no, lanza 400. Recibe el conductor_id."""
    conductor = usuario_repository.obtener_por_id(db, conductor_id)
    if conductor is None or conductor.rol != "conductor" or not conductor.estado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El conductor indicado no existe o no está activo",
        )
    return conductor


def crear_vehiculo(db: Session, datos: VehiculoCreate):
    """Registra un vehículo; rechaza placas repetidas y, si viene con conductor, le libera el vehículo anterior (C09-01)."""
    if vehiculo_repository.obtener_por_placa(db, datos.placa):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un vehículo con esa placa",
        )
    if datos.conductor_id is not None:
        validar_conductor_activo(db, datos.conductor_id)
        vehiculo_repository.liberar_otros_de(db, datos.conductor_id)
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
    """Edita campos del vehículo y/o reasigna conductor. Recibe id y campos a cambiar."""
    vehiculo = vehiculo_repository.obtener_por_id(db, vehiculo_id)
    if vehiculo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehículo no encontrado")

    campos = datos.model_dump(exclude_unset=True)

    for campo in ("marca", "capacidad_volumetrica", "capacidad_cajas"):
        if campo in campos:
            setattr(vehiculo, campo, campos[campo])

    if "conductor_id" in campos:
        conductor_id = campos["conductor_id"]
        if conductor_id is not None:
            validar_conductor_activo(db, conductor_id)
        vehiculo_repository.reasignar_conductor(db, vehiculo, conductor_id)
    else:
        db.commit()
        db.refresh(vehiculo)

    return _a_dict(vehiculo)


def eliminar_vehiculo(db: Session, vehiculo_id: int) -> dict:
    """Da de baja lógica un vehículo y libera a su conductor. Recibe: id."""
    vehiculo = vehiculo_repository.obtener_por_id(db, vehiculo_id)
    if vehiculo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehículo no encontrado")
    vehiculo_repository.eliminar(db, vehiculo)
    return {"mensaje": "Vehículo eliminado"}
