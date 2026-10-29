# Acceso a datos del modulo de capacidad. Solo consultas y add/delete: el
# servicio decide cuando hacer commit.
from datetime import date
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.capacidad import (
    AuditoriaCapacidad,
    ConfiguracionCapacidad,
    ModeloPersonalizado,
    VinculacionPlaca,
)
from app.models.pedido import Pedido

# Estados que tiene sentido planificar: lo que aun no sale a ruta.
ESTADOS_PLANIFICABLES = ("LISTO_PARA_ENVIO", "ASIGNADO", "POR_RECOGER")


def listar_vinculaciones(db: Session) -> List[VinculacionPlaca]:
    """Devuelve todas las vinculaciones ordenadas por placa. Recibe la sesion."""
    return db.query(VinculacionPlaca).order_by(VinculacionPlaca.placa.asc()).all()


def obtener_vinculacion(db: Session, vinculacion_id: int) -> Optional[VinculacionPlaca]:
    """Busca una vinculacion por id. Recibe la sesion y el id."""
    return db.query(VinculacionPlaca).filter(VinculacionPlaca.id == vinculacion_id).first()


def obtener_vinculacion_por_placa(
    db: Session, placa: str
) -> Optional[VinculacionPlaca]:
    """Busca la vinculacion de una placa. Recibe la sesion y la placa."""
    return (
        db.query(VinculacionPlaca)
        .filter(VinculacionPlaca.placa == placa)
        .first()
    )


def crear_vinculacion(db: Session, vinculacion: VinculacionPlaca) -> VinculacionPlaca:
    """Agrega una vinculacion a la sesion (sin commit). Recibe la sesion y la fila."""
    db.add(vinculacion)
    return vinculacion


def eliminar_vinculacion(db: Session, vinculacion: VinculacionPlaca) -> None:
    """Marca una vinculacion para borrar (sin commit). Recibe la sesion y la fila."""
    db.delete(vinculacion)


def listar_modelos_personalizados(db: Session) -> List[ModeloPersonalizado]:
    """Devuelve ediciones y altas hechas desde el panel. Recibe la sesion."""
    return db.query(ModeloPersonalizado).all()


def obtener_modelo_personalizado(
    db: Session, modelo_id: str
) -> Optional[ModeloPersonalizado]:
    """Busca la fila propia de un modelo. Recibe la sesion y el id."""
    return (
        db.query(ModeloPersonalizado)
        .filter(ModeloPersonalizado.modelo_id == modelo_id)
        .first()
    )


def guardar_modelo_personalizado(
    db: Session, fila: ModeloPersonalizado
) -> ModeloPersonalizado:
    """Agrega o actualiza una fila de modelo (sin commit). Recibe la sesion y la fila."""
    db.add(fila)
    return fila


def eliminar_modelo_personalizado(db: Session, fila: ModeloPersonalizado) -> None:
    """Marca para borrar una fila de modelo (sin commit). Recibe la sesion y la fila."""
    db.delete(fila)


def obtener_configuracion(db: Session) -> Optional[ConfiguracionCapacidad]:
    """Devuelve la fila unica de configuracion (o None). Recibe la sesion."""
    return db.query(ConfiguracionCapacidad).first()


def guardar_configuracion(
    db: Session, configuracion: ConfiguracionCapacidad
) -> ConfiguracionCapacidad:
    """Agrega o actualiza la configuracion (sin commit). Recibe la sesion y la fila."""
    db.add(configuracion)
    return configuracion


def registrar_auditoria(
    db: Session,
    accion: str,
    entidad: str,
    entidad_id: Optional[str],
    detalle: Optional[str],
    usuario: str,
) -> AuditoriaCapacidad:
    """Agrega una fila de auditoria (sin commit). Recibe accion, entidad y usuario."""
    fila = AuditoriaCapacidad(
        accion=accion,
        entidad=entidad,
        entidad_id=str(entidad_id) if entidad_id is not None else None,
        detalle=detalle,
        usuario=usuario,
    )
    db.add(fila)
    return fila


def listar_auditoria(db: Session, limite: int = 100) -> List[AuditoriaCapacidad]:
    """Devuelve los ultimos movimientos del modulo. Recibe la sesion y el limite."""
    return (
        db.query(AuditoriaCapacidad)
        .order_by(AuditoriaCapacidad.id.desc())
        .limit(limite)
        .all()
    )


def listar_pedidos_planificables(
    db: Session,
    pedido_ids: Optional[List[int]] = None,
    estado: Optional[str] = None,
    distrito: Optional[str] = None,
    fecha: Optional[date] = None,
    limite: int = 5000,
) -> List[Pedido]:
    """Consulta pedidos para la calculadora. Recibe ids o filtros y un tope.

    No escribe nada: el modulo solo lee pedidos del nucleo.
    """
    consulta = db.query(Pedido)

    if pedido_ids:
        consulta = consulta.filter(Pedido.id.in_(pedido_ids))
    else:
        if estado:
            consulta = consulta.filter(Pedido.estado == estado)
        else:
            consulta = consulta.filter(Pedido.estado.in_(ESTADOS_PLANIFICABLES))
        if distrito:
            consulta = consulta.filter(Pedido.distrito == distrito)
        if fecha:
            consulta = consulta.filter(func.date(Pedido.fecha_creacion) == fecha)

    return consulta.order_by(Pedido.id.asc()).limit(limite).all()