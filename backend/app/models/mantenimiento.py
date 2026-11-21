# Tablas propias del modulo de mantenimiento y documentos de la flota (Idea 4).
# Viven fuera de las tablas del nucleo: el modulo solo LEE vehiculos y guarda
# sus propios registros, documentos, configuracion y auditoria.
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)

from app.db.database import Base


class DocumentoFlota(Base):
    """Documento legal u operativo de un vehiculo (SOAT, revision tecnica, etc.).

    Se guardan varias filas por vehiculo y tipo: cada renovacion es un registro
    nuevo. El estado (VIGENTE / POR_VENCER / VENCIDO) no se guarda: se calcula
    con la fecha de vencimiento y los dias de aviso configurados.
    """

    __tablename__ = "mantenimiento_documentos"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), unique=True, index=True, nullable=True)  # DC-001
    vehiculo_id = Column(Integer, ForeignKey("vehiculos.id"), nullable=False, index=True)
    placa = Column(String(20), nullable=False, index=True)  # copia legible para el historial

    tipo_documento = Column(String(30), nullable=False, index=True)
    numero = Column(String(60), nullable=False)
    entidad_emisora = Column(String(120), nullable=True)
    fecha_emision = Column(Date, nullable=False)
    fecha_vencimiento = Column(Date, nullable=False, index=True)
    archivo_url = Column(String(300), nullable=True)
    observaciones = Column(Text, nullable=True)

    creado_por = Column(String(150), nullable=False)
    creado_en = Column(DateTime, default=datetime.utcnow, nullable=False)
    actualizado_por = Column(String(150), nullable=True)
    actualizado_en = Column(DateTime, nullable=True)
    eliminado_en = Column(DateTime, nullable=True)  # borrado logico


class MantenimientoRegistro(Base):
    """Orden o registro de mantenimiento preventivo/correctivo de un vehiculo."""

    __tablename__ = "mantenimiento_registros"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), unique=True, index=True, nullable=True)  # MT-001
    vehiculo_id = Column(Integer, ForeignKey("vehiculos.id"), nullable=False, index=True)
    placa = Column(String(20), nullable=False, index=True)

    tipo = Column(String(20), nullable=False, default="PREVENTIVO")
    categoria = Column(String(30), nullable=False, default="REVISION_GENERAL")
    descripcion = Column(Text, nullable=False)
    prioridad = Column(String(10), nullable=False, default="MEDIA")
    estado = Column(String(20), nullable=False, default="PROGRAMADO", index=True)

    fecha_programada = Column(Date, nullable=True, index=True)
    fecha_ejecucion = Column(Date, nullable=True)
    kilometraje = Column(Integer, nullable=True)
    costo = Column(Float, nullable=True)
    moneda = Column(String(3), nullable=False, default="PEN")
    taller = Column(String(120), nullable=True)
    observaciones = Column(Text, nullable=True)

    creado_por = Column(String(150), nullable=False)
    creado_en = Column(DateTime, default=datetime.utcnow, nullable=False)
    actualizado_por = Column(String(150), nullable=True)
    actualizado_en = Column(DateTime, nullable=True)
    eliminado_en = Column(DateTime, nullable=True)  # borrado logico


class PlanPreventivo(Base):
    """Plan de mantenimiento preventivo por vehiculo, categoria, km y tiempo.

    El estado no se guarda: se calcula con el kilometraje real (rutas finalizadas
    y lecturas del odometro) y con la fecha base del plan.
    """

    __tablename__ = "mantenimiento_preventivos"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), unique=True, index=True, nullable=True)  # PV-001
    vehiculo_id = Column(Integer, ForeignKey("vehiculos.id"), nullable=False, index=True)
    placa = Column(String(20), nullable=False, index=True)

    categoria = Column(String(30), nullable=False, index=True)
    descripcion = Column(Text, nullable=False)
    intervalo_km = Column(Integer, nullable=False)
    intervalo_dias = Column(Integer, nullable=True)
    km_base = Column(Integer, nullable=True)
    fecha_base = Column(Date, nullable=True, index=True)
    activo = Column(Boolean, nullable=False, default=True)

    creado_por = Column(String(150), nullable=False)
    creado_en = Column(DateTime, default=datetime.utcnow, nullable=False)
    actualizado_por = Column(String(150), nullable=True)
    actualizado_en = Column(DateTime, nullable=True)
    eliminado_en = Column(DateTime, nullable=True)  # borrado logico


class CargaCombustible(Base):
    """Carga de combustible de una unidad. Sirve para calcular rendimiento y costos."""

    __tablename__ = "mantenimiento_combustible"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), unique=True, index=True, nullable=True)  # CB-001
    vehiculo_id = Column(Integer, ForeignKey("vehiculos.id"), nullable=False, index=True)
    placa = Column(String(20), nullable=False, index=True)

    fecha = Column(Date, nullable=False, index=True)
    tipo_combustible = Column(String(20), nullable=False, default="DIESEL")
    galones = Column(Float, nullable=False)
    monto = Column(Float, nullable=False)
    odometro = Column(Integer, nullable=True)
    proveedor = Column(String(120), nullable=True)
    observaciones = Column(Text, nullable=True)

    creado_por = Column(String(150), nullable=False)
    creado_en = Column(DateTime, default=datetime.utcnow, nullable=False)
    actualizado_por = Column(String(150), nullable=True)
    actualizado_en = Column(DateTime, nullable=True)
    eliminado_en = Column(DateTime, nullable=True)  # borrado logico


class ConfiguracionMantenimiento(Base):
    """Parametros del modulo. Es una sola fila (id=1)."""

    __tablename__ = "mantenimiento_configuracion"

    id = Column(Integer, primary_key=True)
    dias_aviso_documento = Column(Integer, nullable=False, default=30)
    dias_aviso_mantenimiento = Column(Integer, nullable=False, default=7)
    moneda = Column(String(3), nullable=False, default="PEN")
    alertas_documentos = Column(Boolean, nullable=False, default=True)
    alertas_mantenimientos = Column(Boolean, nullable=False, default=True)
    tolerancia_consumo = Column(Integer, nullable=False, default=20)  # % para consumo anomalo
    actualizado_por = Column(String(150), nullable=True)
    actualizado_en = Column(DateTime, nullable=True)


class AuditoriaMantenimiento(Base):
    """Registro de cambios del modulo (quien hizo que y cuando)."""

    __tablename__ = "mantenimiento_auditoria"

    id = Column(Integer, primary_key=True, index=True)
    accion = Column(String(40), nullable=False)
    entidad = Column(String(40), nullable=False)
    entidad_id = Column(String(80), nullable=True)
    detalle = Column(Text, nullable=True)
    usuario = Column(String(150), nullable=False)
    creado_en = Column(DateTime, default=datetime.utcnow, nullable=False)
