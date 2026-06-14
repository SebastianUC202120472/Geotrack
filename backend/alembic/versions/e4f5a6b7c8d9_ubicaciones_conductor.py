"""Tabla ubicaciones_conductor (mapa de flota en tiempo real)

Revision ID: e4f5a6b7c8d9
Revises: c3d4e5f6a7b8
Create Date: 2026-06-14 12:00:00.000000

Guarda la última posición conocida de cada conductor (una fila por conductor,
se sobrescribe en cada envío) para pintar el mapa de la flota en el panel admin.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e4f5a6b7c8d9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'ubicaciones_conductor',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conductor_id', sa.Integer(), nullable=False),
        sa.Column('latitud', sa.Float(), nullable=False),
        sa.Column('longitud', sa.Float(), nullable=False),
        sa.Column('actualizado_en', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['conductor_id'], ['usuarios.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_ubicaciones_conductor_id'), 'ubicaciones_conductor', ['id'])
    op.create_index(op.f('ix_ubicaciones_conductor_conductor_id'), 'ubicaciones_conductor', ['conductor_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_ubicaciones_conductor_conductor_id'), table_name='ubicaciones_conductor')
    op.drop_index(op.f('ix_ubicaciones_conductor_id'), table_name='ubicaciones_conductor')
    op.drop_table('ubicaciones_conductor')
