# Acceso a datos del modulo de mantenimiento y documentos (Idea 4).
# Solo consultas y operaciones de agregar/actualizar. El servicio decide
# cuando ejecutar commit y cuando registrar auditoria.
from datetime import date, datetime, time
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.conductor import PerfilConductor
from app.models.incidencia import Incidencia
from app.models.mantenimiento import (
    AuditoriaMantenimiento,
    CargaCombustible,
    ConfiguracionMantenimiento,
    DocumentoFlota,
    MantenimientoRegistro,
    PlanPreventivo,
)
from app.models.ruta import Ruta
from app.models.usuario import Usuario


# ============================================================
# DOCUMENTOS DE LA FLOTA
# ============================================================


def listar_documentos(
    db: Session,
    placa: Optional[str] = None,
    tipo_documento: Optional[str] = None,
) -> List[DocumentoFlota]:
    """Devuelve los documentos activos, con filtros opcionales. Recibe la sesion."""

    consulta = db.query(DocumentoFlota).filter(DocumentoFlota.eliminado_en.is_(None))
    if placa:
        consulta = consulta.filter(DocumentoFlota.placa == placa)
    if tipo_documento:
        consulta = consulta.filter(DocumentoFlota.tipo_documento == tipo_documento)
    return (
        consulta.order_by(
            DocumentoFlota.fecha_vencimiento.asc(),
            DocumentoFlota.id.asc(),
        )
        .all()
    )


def obtener_documento(db: Session, documento_id: int) -> Optional[DocumentoFlota]:
    """Busca un documento activo por su identificador. Recibe la sesion y el id."""

    return (
        db.query(DocumentoFlota)
        .filter(
            DocumentoFlota.id == documento_id,
            DocumentoFlota.eliminado_en.is_(None),
        )
        .first()
    )


def buscar_documento_duplicado(
    db: Session,
    vehiculo_id: int,
    tipo_documento: str,
    numero: str,
    excluir_id: Optional[int] = None,
) -> Optional[DocumentoFlota]:
    """Busca un documento activo con la misma placa, tipo y numero.

    Sirve para no registrar dos veces el mismo SOAT o la misma revision tecnica.
    El numero distinto permite guardar renovaciones del mismo tipo.
    """

    consulta = db.query(DocumentoFlota).filter(
        DocumentoFlota.vehiculo_id == vehiculo_id,
        DocumentoFlota.tipo_documento == tipo_documento,
        DocumentoFlota.numero == numero,
        DocumentoFlota.eliminado_en.is_(None),
    )
    if excluir_id is not None:
        consulta = consulta.filter(DocumentoFlota.id != excluir_id)
    return consulta.first()


def crear_documento(db: Session, fila: DocumentoFlota) -> DocumentoFlota:
    """Agrega un documento a la sesion. El commit lo hace el servicio."""

    db.add(fila)
    return fila


# ============================================================
# MANTENIMIENTOS
# ============================================================


def listar_mantenimientos(
    db: Session,
    placa: Optional[str] = None,
    tipo: Optional[str] = None,
    estado: Optional[str] = None,
    desde: Optional[date] = None,
    hasta: Optional[date] = None,
    limite: int = 500,
) -> List[MantenimientoRegistro]:
    """Devuelve mantenimientos activos con filtros opcionales. Recibe la sesion."""

    consulta = db.query(MantenimientoRegistro).filter(
        MantenimientoRegistro.eliminado_en.is_(None)
    )
    if placa:
        consulta = consulta.filter(MantenimientoRegistro.placa == placa)
    if tipo:
        consulta = consulta.filter(MantenimientoRegistro.tipo == tipo)
    if estado:
        consulta = consulta.filter(MantenimientoRegistro.estado == estado)
    if desde is not None:
        consulta = consulta.filter(MantenimientoRegistro.fecha_programada >= desde)
    if hasta is not None:
        consulta = consulta.filter(MantenimientoRegistro.fecha_programada <= hasta)
    return (
        consulta.order_by(
            MantenimientoRegistro.fecha_programada.asc(),
            MantenimientoRegistro.id.asc(),
        )
        .limit(limite)
        .all()
    )


def obtener_mantenimiento(
    db: Session, mantenimiento_id: int
) -> Optional[MantenimientoRegistro]:
    """Busca un mantenimiento activo por su identificador. Recibe la sesion y el id."""

    return (
        db.query(MantenimientoRegistro)
        .filter(
            MantenimientoRegistro.id == mantenimiento_id,
            MantenimientoRegistro.eliminado_en.is_(None),
        )
        .first()
    )


def crear_mantenimiento(
    db: Session, fila: MantenimientoRegistro
) -> MantenimientoRegistro:
    """Agrega un mantenimiento a la sesion. El commit lo hace el servicio."""

    db.add(fila)
    return fila


# ============================================================
# CONFIGURACION
# ============================================================


def obtener_configuracion(db: Session) -> Optional[ConfiguracionMantenimiento]:
    """Devuelve la fila unica de configuracion, si existe. Recibe la sesion."""

    return db.query(ConfiguracionMantenimiento).first()


def guardar_configuracion(
    db: Session, configuracion: ConfiguracionMantenimiento
) -> ConfiguracionMantenimiento:
    """Agrega o actualiza la configuracion en la sesion. Recibe la fila."""

    db.add(configuracion)
    return configuracion


# ============================================================
# AUDITORIA
# ============================================================


def registrar_auditoria(
    db: Session,
    accion: str,
    entidad: str,
    entidad_id: Optional[str],
    detalle: Optional[str],
    usuario: str,
) -> AuditoriaMantenimiento:
    """Registra una operacion del modulo. Recibe accion, entidad y usuario."""

    fila = AuditoriaMantenimiento(
        accion=accion,
        entidad=entidad,
        entidad_id=str(entidad_id) if entidad_id is not None else None,
        detalle=detalle,
        usuario=usuario,
    )
    db.add(fila)
    return fila


def listar_auditoria(db: Session, limite: int = 100) -> List[AuditoriaMantenimiento]:
    """Devuelve los movimientos recientes del modulo. Recibe la sesion y el limite."""

    return (
        db.query(AuditoriaMantenimiento)
        .order_by(AuditoriaMantenimiento.id.desc())
        .limit(limite)
        .all()
    )


# ============================================================
# LICENCIAS DE CONDUCTORES (solo lectura del nucleo)
# ============================================================


def listar_licencias(db: Session):
    """Devuelve los perfiles de conductor con su usuario. Solo lee el nucleo.

    La licencia vive en el nucleo (conductor_perfiles); el modulo no la modifica,
    solo la consulta para calcular vencimientos y alertas.
    """

    return (
        db.query(PerfilConductor, Usuario)
        .join(Usuario, Usuario.id == PerfilConductor.usuario_id)
        .order_by(PerfilConductor.licencia_vencimiento.asc(), PerfilConductor.id.asc())
        .all()
    )


# ============================================================
# PLANES PREVENTIVOS (semana 14)
# ============================================================


def listar_preventivos(
    db: Session,
    placa: Optional[str] = None,
    categoria: Optional[str] = None,
    limite: int = 500,
) -> List[PlanPreventivo]:
    """Devuelve los planes activos con filtros opcionales. Recibe la sesion."""

    consulta = db.query(PlanPreventivo).filter(
        PlanPreventivo.eliminado_en.is_(None)
    )
    if placa:
        consulta = consulta.filter(PlanPreventivo.placa == placa)
    if categoria:
        consulta = consulta.filter(PlanPreventivo.categoria == categoria)
    return (
        consulta.order_by(PlanPreventivo.placa.asc(), PlanPreventivo.id.asc())
        .limit(limite)
        .all()
    )


def obtener_preventivo(db: Session, preventivo_id: int) -> Optional[PlanPreventivo]:
    """Busca un plan activo por su identificador. Recibe la sesion y el id."""

    return (
        db.query(PlanPreventivo)
        .filter(
            PlanPreventivo.id == preventivo_id,
            PlanPreventivo.eliminado_en.is_(None),
        )
        .first()
    )


def crear_preventivo(db: Session, fila: PlanPreventivo) -> PlanPreventivo:
    """Agrega un plan a la sesion. El commit lo hace el servicio."""

    db.add(fila)
    return fila


# ============================================================
# COMBUSTIBLE (semana 14)
# ============================================================


def listar_cargas(
    db: Session,
    placa: Optional[str] = None,
    tipo_combustible: Optional[str] = None,
    desde: Optional[date] = None,
    hasta: Optional[date] = None,
    limite: int = 500,
) -> List[CargaCombustible]:
    """Devuelve las cargas activas con filtros opcionales. Recibe la sesion."""

    consulta = db.query(CargaCombustible).filter(
        CargaCombustible.eliminado_en.is_(None)
    )
    if placa:
        consulta = consulta.filter(CargaCombustible.placa == placa)
    if tipo_combustible:
        consulta = consulta.filter(
            CargaCombustible.tipo_combustible == tipo_combustible
        )
    if desde is not None:
        consulta = consulta.filter(CargaCombustible.fecha >= desde)
    if hasta is not None:
        consulta = consulta.filter(CargaCombustible.fecha <= hasta)
    return (
        consulta.order_by(CargaCombustible.fecha.asc(), CargaCombustible.id.asc())
        .limit(limite)
        .all()
    )


def obtener_carga(db: Session, carga_id: int) -> Optional[CargaCombustible]:
    """Busca una carga activa por su identificador. Recibe la sesion y el id."""

    return (
        db.query(CargaCombustible)
        .filter(
            CargaCombustible.id == carga_id,
            CargaCombustible.eliminado_en.is_(None),
        )
        .first()
    )


def crear_carga(db: Session, fila: CargaCombustible) -> CargaCombustible:
    """Agrega una carga a la sesion. El commit lo hace el servicio."""

    db.add(fila)
    return fila


# ============================================================
# SOLO LECTURA: KM DE RUTAS E INCIDENCIAS DEL NUCLEO (semana 14)
# ============================================================


def kilometraje_rutas(
    db: Session,
    placa: str,
    desde: Optional[date] = None,
    hasta: Optional[date] = None,
) -> float:
    """Suma los km de las rutas finalizadas de una placa. Solo lee el nucleo.

    El kilometraje real del sistema esta en Ruta.km_estimado (calculo Haversine
    guardado al optimizar o al finalizar la ruta). Este modulo no lo modifica.
    """

    consulta = db.query(func.coalesce(func.sum(Ruta.km_estimado), 0.0)).filter(
        Ruta.vehiculo_placa == placa,
        Ruta.estado == "FINALIZADA",
    )
    if desde is not None:
        consulta = consulta.filter(Ruta.fecha_fin >= datetime.combine(desde, time.min))
    if hasta is not None:
        consulta = consulta.filter(Ruta.fecha_fin <= datetime.combine(hasta, time.max))
    return float(consulta.scalar() or 0.0)


def listar_incidencias(db: Session, placa: Optional[str] = None) -> List[Incidencia]:
    """Devuelve incidencias del nucleo, opcionalmente por placa. Solo lectura."""

    consulta = db.query(Incidencia)
    if placa:
        consulta = consulta.filter(Incidencia.vehiculo_placa == placa)
    return consulta.order_by(Incidencia.creado_en.desc()).all()