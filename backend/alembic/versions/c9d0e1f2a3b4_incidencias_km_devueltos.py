"""Incidencias (CUS-30) y km de eficiencia en rutas (CUS-34)

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
Create Date: 2026-06-21 10:00:00.000000

- incidencias: auxilio mecánico que reporta el conductor (CUS-30). Mientras una está
  ABIERTA, su ruta se considera PAUSADA.
- rutas.km_estimado / rutas.km_ahorrado: métricas estimadas al optimizar (CUS-34).

El estado CANCELADO de pedidos (CUS-31) NO requiere cambios de esquema (es un valor más
de la columna 'estado'). Los parámetros de combustible se siembran en código (main.py).
En BDs nuevas todo lo crea Base.metadata.create_all; esta migración cubre las gestionadas
por Alembic.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c9d0e1f2a3b4'
down_revision: Union[str, None] = 'b8c9d0e1f2a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'incidencias',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('codigo', sa.String(length=20), nullable=True),
        sa.Column('ruta_id', sa.Integer(), nullable=False),
        sa.Column('conductor_id', sa.Integer(), nullable=False),
        sa.Column('vehiculo_placa', sa.String(length=20), nullable=True),
        sa.Column('tipo', sa.String(length=40), nullable=True),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('url_evidencia', sa.String(length=255), nullable=True),
        sa.Column('latitud', sa.Float(), nullable=True),
        sa.Column('longitud', sa.Float(), nullable=True),
        sa.Column('estado', sa.String(length=20), nullable=True),
        sa.Column('creado_en', sa.DateTime(), nullable=True),
        sa.Column('resuelto_en', sa.DateTime(), nullable=True),
        sa.Column('resuelto_por', sa.Integer(), nullable=True),
        sa.Column('nota_resolucion', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['ruta_id'], ['rutas.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_incidencias_id'), 'incidencias', ['id'], unique=False)
    op.create_index(op.f('ix_incidencias_codigo'), 'incidencias', ['codigo'], unique=True)
    op.create_index(op.f('ix_incidencias_ruta_id'), 'incidencias', ['ruta_id'], unique=False)
    op.create_index(op.f('ix_incidencias_conductor_id'), 'incidencias', ['conductor_id'], unique=False)
    op.create_index(op.f('ix_incidencias_creado_en'), 'incidencias', ['creado_en'], unique=False)

    op.add_column('rutas', sa.Column('km_estimado', sa.Float(), nullable=True))
    op.add_column('rutas', sa.Column('km_ahorrado', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('rutas', 'km_ahorrado')
    op.drop_column('rutas', 'km_estimado')
    op.drop_index(op.f('ix_incidencias_creado_en'), table_name='incidencias')
    op.drop_index(op.f('ix_incidencias_conductor_id'), table_name='incidencias')
    op.drop_index(op.f('ix_incidencias_ruta_id'), table_name='incidencias')
    op.drop_index(op.f('ix_incidencias_codigo'), table_name='incidencias')
    op.drop_index(op.f('ix_incidencias_id'), table_name='incidencias')
    op.drop_table('incidencias')
