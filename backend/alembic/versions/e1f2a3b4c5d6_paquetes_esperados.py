"""Almacén (CUS-14): paquetes_esperados + escaneos_desconocidos

Revision ID: e1f2a3b4c5d6
Revises: d0e1f2a3b4c5
Create Date: 2026-06-21 14:00:00.000000

El estado INGRESADO de solicitudes_recojo (CUS-14) NO requiere cambio de esquema
(es un valor más de la columna 'estado'). En BD nueva todo lo crea create_all.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e1f2a3b4c5d6'
down_revision: Union[str, None] = 'd0e1f2a3b4c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'paquetes_esperados',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('codigo', sa.String(length=50), nullable=False),
        sa.Column('recojo_id', sa.Integer(), nullable=False),
        sa.Column('estado', sa.String(length=20), nullable=True),
        sa.Column('escaneado_en', sa.DateTime(), nullable=True),
        sa.Column('escaneado_por', sa.Integer(), nullable=True),
        sa.Column('creado_en', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['recojo_id'], ['solicitudes_recojo.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_paquetes_esperados_id'), 'paquetes_esperados', ['id'], unique=False)
    op.create_index(op.f('ix_paquetes_esperados_codigo'), 'paquetes_esperados', ['codigo'], unique=False)
    op.create_index(op.f('ix_paquetes_esperados_recojo_id'), 'paquetes_esperados', ['recojo_id'], unique=False)
    op.create_table(
        'escaneos_desconocidos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('recojo_id', sa.Integer(), nullable=False),
        sa.Column('codigo', sa.String(length=50), nullable=False),
        sa.Column('escaneado_en', sa.DateTime(), nullable=True),
        sa.Column('escaneado_por', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['recojo_id'], ['solicitudes_recojo.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_escaneos_desconocidos_id'), 'escaneos_desconocidos', ['id'], unique=False)
    op.create_index(op.f('ix_escaneos_desconocidos_recojo_id'), 'escaneos_desconocidos', ['recojo_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_escaneos_desconocidos_recojo_id'), table_name='escaneos_desconocidos')
    op.drop_index(op.f('ix_escaneos_desconocidos_id'), table_name='escaneos_desconocidos')
    op.drop_table('escaneos_desconocidos')
    op.drop_index(op.f('ix_paquetes_esperados_recojo_id'), table_name='paquetes_esperados')
    op.drop_index(op.f('ix_paquetes_esperados_codigo'), table_name='paquetes_esperados')
    op.drop_index(op.f('ix_paquetes_esperados_id'), table_name='paquetes_esperados')
    op.drop_table('paquetes_esperados')
