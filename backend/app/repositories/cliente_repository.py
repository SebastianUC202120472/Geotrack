# app/repositories/cliente_repository.py
# ============================================================================
# CAPA: REPOSITORIO (acceso a datos) — Clean Architecture
# ----------------------------------------------------------------------------
# ¿QUÉ HACE?  Única capa que consulta/escribe en la tabla 'clientes_corporativos'.
# ¿CON QUÉ SE CONECTA?
#   - models/cliente.py -> la tabla.
#   - Lo USAN: services/cliente_service.py y services/pedido_service.py
#              (este último crea el cliente automáticamente al cargar el Excel).
# ============================================================================
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.cliente import ClienteCorporativo
from app.core.codigos import asignar_codigo, PREFIJO_CLIENTE


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
