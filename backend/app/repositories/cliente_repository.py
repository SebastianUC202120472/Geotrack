# app/repositories/cliente_repository.py
# Única capa que consulta/escribe en la tabla 'clientes_corporativos'.
from datetime import datetime
from typing import List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.cliente import ClienteCorporativo
from app.core.codigos import asignar_codigo, PREFIJO_CLIENTE


def obtener_por_id(db: Session, cliente_id: int) -> Optional[ClienteCorporativo]:
    """Busca un cliente activo por su id (no borrado lógicamente)."""
    return (
        db.query(ClienteCorporativo)
        .filter(ClienteCorporativo.id == cliente_id, ClienteCorporativo.eliminado_en == None)  # noqa: E711
        .first()
    )


def listar(db: Session) -> List[ClienteCorporativo]:
    """Lista los clientes ACTIVOS (no borrados lógicamente)."""
    return (
        db.query(ClienteCorporativo)
        .filter(ClienteCorporativo.eliminado_en == None)  # noqa: E711
        .order_by(ClienteCorporativo.razon_social.asc())
        .all()
    )


def obtener_por_identificador(db: Session, identificador_unico: str) -> Optional[ClienteCorporativo]:
    """Busca un cliente por su RUC (identificador único)."""
    return (
        db.query(ClienteCorporativo)
        .filter(ClienteCorporativo.identificador_unico == identificador_unico)
        .first()
    )


def obtener_por_razon_social(db: Session, razon_social: str) -> Optional[ClienteCorporativo]:
    """Busca un cliente por su razón social (nombre de la empresa)."""
    return (
        db.query(ClienteCorporativo)
        .filter(ClienteCorporativo.razon_social == razon_social)
        .first()
    )


def buscar_por_razon_social_normalizada(db: Session, razon_social: str) -> Optional[ClienteCorporativo]:
    """Busca un cliente ACTIVO por razón social comparando normalizado (sin espacios
    de sobra ni distinguir mayúsculas). Recibe: el texto de la razón social del Excel."""
    objetivo = (razon_social or "").strip().lower()
    if not objetivo:
        return None
    return (
        db.query(ClienteCorporativo)
        .filter(
            ClienteCorporativo.eliminado_en == None,  # noqa: E711
            func.lower(func.trim(ClienteCorporativo.razon_social)) == objetivo,
        )
        .first()
    )


def crear(db: Session, razon_social: str, identificador_unico=None, contacto=None) -> ClienteCorporativo:
    """Crea un cliente y hace flush para obtener su id (sin cerrar la transacción)."""
    cliente = ClienteCorporativo(
        razon_social=razon_social,
        identificador_unico=identificador_unico,
        contacto=contacto,
    )
    db.add(cliente)
    asignar_codigo(db, cliente, PREFIJO_CLIENTE)  # codigo legible CL-001 (hace flush)
    return cliente


def actualizar(db: Session, cliente: ClienteCorporativo, **campos) -> ClienteCorporativo:
    """Edita un cliente aplicando SOLO los campos recibidos (las claves presentes en
    `campos`), incluso si su valor es None (así se puede limpiar RUC/contacto). Recibe:
    el cliente y los campos a cambiar. Devuelve el cliente actualizado."""
    for clave, valor in campos.items():
        setattr(cliente, clave, valor)
    db.commit()
    db.refresh(cliente)
    return cliente


def eliminar(db: Session, cliente: ClienteCorporativo) -> None:
    """Baja lógica de un cliente (marca eliminado_en; conserva su historial). Recibe: el cliente."""
    cliente.eliminado_en = datetime.utcnow()
    db.commit()


def buscar_o_crear(db: Session, razon_social: str, identificador_unico=None, contacto=None) -> ClienteCorporativo:
    """
    Devuelve el cliente existente o lo crea si no está (lo usa la carga de Excel).
    Prioridad de búsqueda: por RUC si viene; si no, por razón social.
    """
    cliente = None
    if identificador_unico:
        cliente = obtener_por_identificador(db, identificador_unico)
    if not cliente:
        cliente = obtener_por_razon_social(db, razon_social)
    if not cliente:
        cliente = crear(db, razon_social, identificador_unico, contacto)
    return cliente
