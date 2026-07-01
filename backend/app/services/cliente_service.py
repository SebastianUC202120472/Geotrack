from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories import cliente_repository
from app.schemas.cliente import ClienteCreate, ClienteUpdate
from app.services.geocoder import obtener_coordenadas


def _distrito_de(direccion: str) -> str:
    """Extrae el distrito de la direccion (texto tras la primera coma). Recibe: cadena de direccion."""
    partes = (direccion or "").split(",", 1)
    return partes[1].strip() if len(partes) > 1 else "ZONA_DESCONOCIDA"


def _geocodificar_origen(direccion: str):
    """Geocodifica la direccion de recojo. Recibe: string de direccion. Devuelve (lat, lng, distrito)."""
    lat, lng = obtener_coordenadas(direccion)
    distrito = _distrito_de(direccion) if lat is not None else None
    return lat, lng, distrito


def _cliente_o_404(db: Session, cliente_id: int):
    """Devuelve el cliente activo o lanza 404. Recibe: sesion db y cliente_id."""
    cliente = cliente_repository.obtener_por_id(db, cliente_id)
    if cliente is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado")
    return cliente


def listar_clientes(db: Session):
    """Lista los clientes activos. Recibe: sesion db."""
    return cliente_repository.listar(db)


def crear_cliente(db: Session, datos: ClienteCreate):
    """Crea un cliente nuevo validando RUC unico y geocodificando la direccion. Recibe: sesion db y datos del cliente."""
    if datos.identificador_unico:
        existente = cliente_repository.obtener_por_identificador(db, datos.identificador_unico)
        if existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un cliente con ese identificador (RUC)",
            )

    lat, lng, distrito = _geocodificar_origen(datos.direccion_origen)

    cliente = cliente_repository.crear(
        db,
        razon_social=datos.razon_social,
        identificador_unico=datos.identificador_unico,
        contacto=datos.contacto,
        direccion_origen=datos.direccion_origen,
        distrito=distrito,
        latitud=lat,
        longitud=lng,
    )
    db.commit()

    db.refresh(cliente)
    return cliente


def actualizar_cliente(db: Session, cliente_id: int, datos: ClienteUpdate):
    """Edita los datos de un cliente; valida RUC unico y re-geocodifica si cambia la direccion. Recibe: sesion db, cliente_id y campos a actualizar."""
    cliente = _cliente_o_404(db, cliente_id)
    campos = datos.model_dump(exclude_unset=True)

    if "razon_social" in campos:
        rs = (campos["razon_social"] or "").strip()
        if len(rs) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La razón social debe tener al menos 3 caracteres",
            )
        campos["razon_social"] = rs

    nuevo_ruc = campos.get("identificador_unico")
    if nuevo_ruc and nuevo_ruc != cliente.identificador_unico:
        otro = cliente_repository.obtener_por_identificador(db, nuevo_ruc)
        if otro and otro.id != cliente.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe otro cliente con ese identificador (RUC)",
            )

    # Si la direccion cambio, sincronizar campos geo; cadena vacia = limpiar coordenadas.
    nueva_dir = campos.get("direccion_origen")
    if nueva_dir is not None and nueva_dir != cliente.direccion_origen:
        if nueva_dir.strip():
            lat, lng, distrito = _geocodificar_origen(nueva_dir)
            campos["distrito"] = distrito
            campos["latitud"] = lat
            campos["longitud"] = lng
        else:
            campos["distrito"] = None
            campos["latitud"] = None
            campos["longitud"] = None

    return cliente_repository.actualizar(db, cliente, **campos)


def eliminar_cliente(db: Session, cliente_id: int) -> dict:
    """Baja logica de un cliente. Recibe: sesion db y cliente_id."""
    cliente = _cliente_o_404(db, cliente_id)
    cliente_repository.eliminar(db, cliente)
    return {"mensaje": "Cliente eliminado"}
