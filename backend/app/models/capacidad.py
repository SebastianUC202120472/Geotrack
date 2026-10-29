# Tablas propias del modulo de catalogo y capacidad (Idea 3).
# Viven fuera de las tablas del nucleo: el modulo solo LEE pedidos y vehiculos.
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from app.db.database import Base


class VinculacionPlaca(Base):
    """Relacion entre una placa de la flota y un modelo del catalogo."""

    __tablename__ = "capacidad_vinculaciones"
    __table_args__ = (
        UniqueConstraint("placa", name="uq_capacidad_vinculacion_placa"),
    )

    id = Column(Integer, primary_key=True, index=True)
    placa = Column(String(10), nullable=False, index=True)
    modelo_id = Column(String(80), nullable=False, index=True)
    creado_por = Column(String(150), nullable=False)
    creado_en = Column(DateTime, default=datetime.utcnow, nullable=False)


class ModeloPersonalizado(Base):
    """Modelo agregado o editado desde el panel.

    Si ``es_nuevo`` es False, la fila es una copia editada de un modelo del JSON
    base. Si es True, el modelo solo existe en la base de datos.
    """

    __tablename__ = "capacidad_modelos_personalizados"

    id = Column(Integer, primary_key=True, index=True)
    modelo_id = Column(String(80), nullable=False, unique=True, index=True)
    es_nuevo = Column(Boolean, nullable=False, default=False)

    marca = Column(String(60), nullable=False)
    modelo = Column(String(80), nullable=False)
    tipo = Column(String(30), nullable=False)
    largo_m = Column(Float, nullable=False)
    ancho_m = Column(Float, nullable=False)
    alto_m = Column(Float, nullable=False)
    volumen_util_m3 = Column(Float, nullable=False)
    carga_util_kg = Column(Float, nullable=False)

    fuente = Column(String(200), nullable=True)
    fuente_url = Column(String(300), nullable=True)
    verificado = Column(Boolean, nullable=False, default=False)

    creado_por = Column(String(150), nullable=False)
    creado_en = Column(DateTime, default=datetime.utcnow, nullable=False)
    actualizado_por = Column(String(150), nullable=True)
    actualizado_en = Column(DateTime, nullable=True)


class ConfiguracionCapacidad(Base):
    """Parametros de planificacion. Es una sola fila (id=1)."""

    __tablename__ = "capacidad_configuracion"

    id = Column(Integer, primary_key=True)
    factor_aprovechamiento = Column(Float, nullable=False, default=0.85)
    max_paradas_por_viaje = Column(Integer, nullable=False, default=25)
    max_paradas_por_jornada = Column(Integer, nullable=False, default=60)
    max_viajes_por_dia = Column(Integer, nullable=False, default=3)
    actualizado_por = Column(String(150), nullable=True)
    actualizado_en = Column(DateTime, nullable=True)


class AuditoriaCapacidad(Base):
    """Registro de cambios del modulo (quien hizo que y cuando)."""

    __tablename__ = "capacidad_auditoria"

    id = Column(Integer, primary_key=True, index=True)
    accion = Column(String(40), nullable=False)
    entidad = Column(String(40), nullable=False)
    entidad_id = Column(String(80), nullable=True)
    detalle = Column(Text, nullable=True)
    usuario = Column(String(150), nullable=False)
    creado_en = Column(DateTime, default=datetime.utcnow, nullable=False)