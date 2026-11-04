
# Acceso a datos del modulo de capacidad.
# Solo consultas y operaciones de agregar/eliminar.
# El servicio decide cuando ejecutar commit.

from datetime import date
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.capacidad import (
    AuditoriaCapacidad,
    ConfiguracionCapacidad,
    ModeloPersonalizado,
    VinculacionPlaca,
)

from app.models.pedido import Pedido


# ============================================================
# ESTADOS PERMITIDOS PARA NUEVOS DESPACHOS
# ============================================================

# Solo se planifican pedidos listos para salir.
# Los pedidos asignados o en ruta no deben duplicarse.

ESTADOS_PLANIFICABLES = ("LISTO_PARA_ENVIO",)


# ============================================================
# VINCULACIONES ENTRE PLACAS Y MODELOS
# ============================================================

def listar_vinculaciones(
    db: Session,
) -> List[VinculacionPlaca]:
    """Devuelve las vinculaciones ordenadas por placa."""

    return (
        db.query(VinculacionPlaca)
        .order_by(VinculacionPlaca.placa.asc())
        .all()
    )


def obtener_vinculacion(
    db: Session,
    vinculacion_id: int,
) -> Optional[VinculacionPlaca]:
    """Busca una vinculacion por su identificador."""

    return (
        db.query(VinculacionPlaca)
        .filter(
            VinculacionPlaca.id == vinculacion_id
        )
        .first()
    )


def obtener_vinculacion_por_placa(
    db: Session,
    placa: str,
) -> Optional[VinculacionPlaca]:
    """Obtiene la vinculacion correspondiente a una placa."""

    return (
        db.query(VinculacionPlaca)
        .filter(
            VinculacionPlaca.placa == placa
        )
        .first()
    )


def crear_vinculacion(
    db: Session,
    vinculacion: VinculacionPlaca,
) -> VinculacionPlaca:
    """Agrega una vinculacion a la sesion.

    El commit se realiza desde el servicio.
    """

    db.add(vinculacion)

    return vinculacion


def eliminar_vinculacion(
    db: Session,
    vinculacion: VinculacionPlaca,
) -> None:
    """Marca una vinculacion para su eliminacion."""

    db.delete(vinculacion)


# ============================================================
# MODELOS PERSONALIZADOS DEL CATALOGO
# ============================================================

def listar_modelos_personalizados(
    db: Session,
) -> List[ModeloPersonalizado]:
    """Devuelve los modelos creados o editados desde el panel."""

    return (
        db.query(ModeloPersonalizado)
        .all()
    )


def obtener_modelo_personalizado(
    db: Session,
    modelo_id: str,
) -> Optional[ModeloPersonalizado]:
    """Busca un modelo personalizado por su identificador."""

    return (
        db.query(ModeloPersonalizado)
        .filter(
            ModeloPersonalizado.modelo_id == modelo_id
        )
        .first()
    )


def guardar_modelo_personalizado(
    db: Session,
    fila: ModeloPersonalizado,
) -> ModeloPersonalizado:
    """Agrega o actualiza un modelo personalizado.

    El servicio controla la transaccion.
    """

    db.add(fila)

    return fila


def eliminar_modelo_personalizado(
    db: Session,
    fila: ModeloPersonalizado,
) -> None:
    """Marca un modelo personalizado para eliminar."""

    db.delete(fila)


# ============================================================
# CONFIGURACION DE CAPACIDAD
# ============================================================

def obtener_configuracion(
    db: Session,
) -> Optional[ConfiguracionCapacidad]:
    """Obtiene la configuracion actual del modulo.

    Incluye factor de aprovechamiento,
    limites de jornada y tamanos S/M/L.
    """

    return (
        db.query(ConfiguracionCapacidad)
        .first()
    )


def guardar_configuracion(
    db: Session,
    configuracion: ConfiguracionCapacidad,
) -> ConfiguracionCapacidad:
    """Guarda o actualiza la configuracion del modulo."""

    db.add(configuracion)

    return configuracion


# ============================================================
# AUDITORIA DE OPERACIONES
# ============================================================

def registrar_auditoria(
    db: Session,
    accion: str,
    entidad: str,
    entidad_id: Optional[str],
    detalle: Optional[str],
    usuario: str,
) -> AuditoriaCapacidad:
    """Registra una operacion realizada en el modulo.

    Guarda la accion, entidad afectada y usuario.
    """

    fila = AuditoriaCapacidad(
        accion=accion,
        entidad=entidad,
        entidad_id=(
            str(entidad_id)
            if entidad_id is not None
            else None
        ),
        detalle=detalle,
        usuario=usuario,
    )

    db.add(fila)

    return fila


def listar_auditoria(
    db: Session,
    limite: int = 100,
) -> List[AuditoriaCapacidad]:
    """Devuelve los movimientos recientes del modulo."""

    return (
        db.query(AuditoriaCapacidad)
        .order_by(
            AuditoriaCapacidad.id.desc()
        )
        .limit(limite)
        .all()
    )


# ============================================================
# CONSULTA DE PEDIDOS PARA PLANIFICACION
# ============================================================

def listar_pedidos_planificables(
    db: Session,
    pedido_ids: Optional[List[int]] = None,
    estado: Optional[str] = None,
    distrito: Optional[str] = None,
    fecha: Optional[date] = None,
    limite: int = 5000,
) -> List[Pedido]:
    """Consulta pedidos disponibles para nuevos despachos.

    No modifica la informacion del nucleo de GeoTrack.

    Permite consultar por identificadores, distrito,
    estado y fecha de creacion.

    Aplica el maximo permitido de pedidos.
    """

    if estado and estado not in ESTADOS_PLANIFICABLES:
        raise HTTPException(
            status_code=422,
            detail=(
                "Solo se planifican pedidos "
                "LISTO_PARA_ENVIO."
            ),
        )

    if limite < 1 or limite > 5000:
        raise HTTPException(
            status_code=422,
            detail=(
                "El limite debe estar "
                "entre 1 y 5000 pedidos."
            ),
        )

    # Se consultan los pedidos del nucleo
    # exclusivamente en modo lectura.

    consulta = (
        db.query(Pedido)
        .filter(
            Pedido.estado.in_(
                ESTADOS_PLANIFICABLES
            )
        )
    )

    # Filtro por identificadores especificos.
    if pedido_ids is not None:
        if not pedido_ids:
            return []

        consulta = consulta.filter(
            Pedido.id.in_(pedido_ids)
        )

    else:
        # Filtro opcional por estado.
        if estado:
            consulta = consulta.filter(
                Pedido.estado == estado
            )

        # Filtro opcional por distrito.
        if distrito:
            consulta = consulta.filter(
                Pedido.distrito == distrito
            )

        # Filtro opcional por fecha de creacion.
        if fecha:
            consulta = consulta.filter(
                func.date(
                    Pedido.fecha_creacion
                ) == fecha
            )

    # Orden estable y limite de registros.
    return (
        consulta
        .order_by(
            Pedido.id.asc()
        )
        .limit(limite)
        .all()
    )
