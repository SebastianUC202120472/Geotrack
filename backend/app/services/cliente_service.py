# app/services/cliente_service.py
# Lógica del módulo de Clientes Corporativos.
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories import cliente_repository
from app.schemas.cliente import ClienteCreate


def listar_clientes(db: Session):
    """Devuelve los clientes activos."""
    return cliente_repository.listar(db)


def crear_cliente(db: Session, datos: ClienteCreate):
    """Registra un cliente nuevo; rechaza si el RUC ya existe."""
    if datos.identificador_unico:
        existente = cliente_repository.obtener_por_identificador(db, datos.identificador_unico)
        if existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un cliente con ese identificador (RUC)",
            )

    cliente = cliente_repository.crear(
        db,
        razon_social=datos.razon_social,
        identificador_unico=datos.identificador_unico,
        contacto=datos.contacto,
    )
    db.commit()          # crear() solo hizo flush; aquí confirmamos
    db.refresh(cliente)
    return cliente
