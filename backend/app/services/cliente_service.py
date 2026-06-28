# app/services/cliente_service.py
# Lógica del módulo de Clientes Corporativos.
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories import cliente_repository
from app.schemas.cliente import ClienteCreate, ClienteUpdate
from app.services.geocoder import obtener_coordenadas


def _distrito_de(direccion: str) -> str:
    """Deriva el distrito del texto de la dirección: lo que va tras la primera coma."""
    partes = (direccion or "").split(",", 1)
    return partes[1].strip() if len(partes) > 1 else "ZONA_DESCONOCIDA"


def _geocodificar_origen(direccion: str):
    """Geocodifica la dirección de recojo del cliente. Devuelve (lat, lng, distrito)."""
    lat, lng = obtener_coordenadas(direccion)
    distrito = _distrito_de(direccion) if lat is not None else None
    return lat, lng, distrito


def _cliente_o_404(db: Session, cliente_id: int):
    """Devuelve el cliente activo o lanza 404 si no existe / está dado de baja."""
    cliente = cliente_repository.obtener_por_id(db, cliente_id)
    if cliente is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado")
    return cliente


def listar_clientes(db: Session):
    """Devuelve los clientes activos."""
    return cliente_repository.listar(db)


def crear_cliente(db: Session, datos: ClienteCreate):
    """Registra un cliente nuevo; rechaza si el RUC ya existe. Geocodifica la dirección de recojo."""
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
    db.commit()          # crear() solo hizo flush; aquí confirmamos
    db.refresh(cliente)
    return cliente


def actualizar_cliente(db: Session, cliente_id: int, datos: ClienteUpdate):
    """CUS-07: edita una empresa cliente. Recibe: id y los campos a cambiar. Si cambia
    el RUC, valida que no choque con otro cliente."""
    cliente = _cliente_o_404(db, cliente_id)
    campos = datos.model_dump(exclude_unset=True)  # solo lo que el cliente envió

    # La razón social, si se envía, no puede quedar vacía (es obligatoria).
    if "razon_social" in campos:
        rs = (campos["razon_social"] or "").strip()
        if len(rs) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La razón social debe tener al menos 3 caracteres",
            )
        campos["razon_social"] = rs

    # Si cambia el RUC (a un valor no vacío), validar que no choque con otro cliente.
    nuevo_ruc = campos.get("identificador_unico")
    if nuevo_ruc and nuevo_ruc != cliente.identificador_unico:
        otro = cliente_repository.obtener_por_identificador(db, nuevo_ruc)
        if otro and otro.id != cliente.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe otro cliente con ese identificador (RUC)",
            )

    # Si la dirección de recojo viene y cambió, re-geocodificar y actualizar los 4 campos.
    nueva_dir = campos.get("direccion_origen")
    if nueva_dir and nueva_dir != cliente.direccion_origen:
        lat, lng, distrito = _geocodificar_origen(nueva_dir)
        campos["distrito"] = distrito
        campos["latitud"] = lat
        campos["longitud"] = lng

    return cliente_repository.actualizar(db, cliente, **campos)


def eliminar_cliente(db: Session, cliente_id: int) -> dict:
    """CUS-07: da de baja (lógica) una empresa cliente. Recibe: id."""
    cliente = _cliente_o_404(db, cliente_id)
    cliente_repository.eliminar(db, cliente)
    return {"mensaje": "Cliente eliminado"}
