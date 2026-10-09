import re
import secrets

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.repositories import cliente_repository
from app.schemas.cliente import ClienteCreate, ClienteUpdate, UbicacionClienteIn, digito_ruc_valido
from app.services.geocoder import obtener_coordenadas


def _slug_codigo(razon_social: str, cliente_id: int) -> str:
    """Deriva un codigo de acceso UNICO desde la razon social. Recibe la razon social y el id.
    El sufijo con el id del cliente garantiza unicidad (evita colisiones del indice unico
    cuando dos razones sociales truncan al mismo prefijo)."""
    base = re.sub(r"[^A-Za-z0-9]", "", (razon_social or "EMP").upper())[:8] or "EMP"
    return f"{base}-{cliente_id}"


def _distrito_de(direccion: str) -> str:
    """Extrae el distrito de la direccion (texto tras la primera coma). Recibe: cadena de direccion."""
    partes = (direccion or "").split(",", 1)
    return partes[1].strip() if len(partes) > 1 else "ZONA_DESCONOCIDA"


def _geocodificar_origen(direccion: str):
    """Geocodifica la direccion de recojo. Recibe: string de direccion. Devuelve (lat, lng, distrito)."""
    lat, lng = obtener_coordenadas(direccion)
    distrito = _distrito_de(direccion) if lat is not None else None
    return lat, lng, distrito


def _exigir_digito_ruc(ruc) -> None:
    """Rechaza un RUC cuyo digito verificador no cuadra (C07-01). Recibe el RUC ya normalizado (o None)."""
    if ruc and not digito_ruc_valido(ruc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El RUC no es válido: revisa los 11 dígitos (el dígito verificador no coincide)",
        )


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
    _exigir_digito_ruc(datos.identificador_unico)
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

    if "razon_social" in campos and not campos["razon_social"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La razón social debe tener al menos 3 caracteres",
        )

    nuevo_ruc = campos.get("identificador_unico")
    if nuevo_ruc and nuevo_ruc != cliente.identificador_unico:
        # Solo se exige el digito verificador si el RUC cambia: asi un RUC historico no bloquea la edicion.
        _exigir_digito_ruc(nuevo_ruc)
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
    """Baja logica de un cliente; tambien le quita el acceso al portal (C07-03). Recibe: sesion db y cliente_id."""
    cliente = _cliente_o_404(db, cliente_id)
    cliente.acceso_activo = False
    cliente_repository.eliminar(db, cliente)
    return {"mensaje": "Cliente eliminado"}


def reintentar_ubicacion(db: Session, cliente_id: int):
    """Vuelve a geocodificar la direccion de recojo del cliente (C07-02). Recibe: sesion db y cliente_id."""
    cliente = _cliente_o_404(db, cliente_id)
    if not (cliente.direccion_origen or "").strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El cliente no tiene dirección de recojo")
    lat, lng, distrito = _geocodificar_origen(cliente.direccion_origen)
    if lat is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Tampoco se pudo ubicar ahora. Corrige la dirección o marca el punto en el mapa.",
        )
    return cliente_repository.actualizar(db, cliente, latitud=lat, longitud=lng, distrito=distrito)


def fijar_ubicacion(db: Session, cliente_id: int, datos: UbicacionClienteIn):
    """Guarda el punto de recojo marcado a mano en el mapa (C07-02). Recibe: sesion db, cliente_id y coordenadas."""
    cliente = _cliente_o_404(db, cliente_id)
    return cliente_repository.actualizar(
        db, cliente, latitud=datos.latitud, longitud=datos.longitud,
        distrito=cliente.distrito or _distrito_de(cliente.direccion_origen),
    )


def generar_acceso_portal(db: Session, cliente_id: int, correo_portal: str) -> dict:
    """Genera/reinicia el acceso al portal de un cliente. Recibe id y correo del portal.
    Devuelve {codigoAcceso, clave} con la clave en claro UNA sola vez."""
    cliente = _cliente_o_404(db, cliente_id)
    codigo = cliente.codigo_acceso or _slug_codigo(cliente.razon_social, cliente.id)
    clave = secrets.token_urlsafe(9)
    cliente.codigo_acceso = codigo
    cliente.clave_hash = get_password_hash(clave)
    cliente.correo_portal = str(correo_portal).strip().lower()
    cliente.acceso_activo = True
    db.commit()
    return {"codigoAcceso": codigo, "clave": clave}


def revocar_acceso_portal(db: Session, cliente_id: int) -> dict:
    """Revoca el acceso al portal de un cliente (no borra credenciales). Recibe el id."""
    cliente = _cliente_o_404(db, cliente_id)
    cliente.acceso_activo = False
    db.commit()
    return {"ok": True}
