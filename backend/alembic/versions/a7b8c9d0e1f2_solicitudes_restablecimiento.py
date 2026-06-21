"""Solicitudes de restablecimiento de contraseña (extra CUS-04)

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-06-20 13:00:00.000000

Tabla para que el conductor pida (desde el Login) que el admin le restablezca la
contraseña. En BDs nuevas la crea Base.metadata.create_all (app/main.py); esta
migración cubre los entornos ya gestionados por Alembic.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7b8c9d0e1f2'
down_revision: Union[str, None] = 'f6a7b8c9d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'solicitudes_restablecimiento',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conductor_id', sa.Integer(), nullable=False),
        sa.Column('correo', sa.String(length=120), nullable=False),
        sa.Column('estado', sa.String(length=20), nullable=True),
        sa.Column('fecha_solicitud', sa.DateTime(), nullable=True),
        sa.Column('fecha_atencion', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['conductor_id'], ['usuarios.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_solicitudes_restablecimiento_id'), 'solicitudes_restablecimiento', ['id'], unique=False)
    op.create_index(op.f('ix_solicitudes_restablecimiento_conductor_id'), 'solicitudes_restablecimiento', ['conductor_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_solicitudes_restablecimiento_conductor_id'), table_name='solicitudes_restablecimiento')
    op.drop_index(op.f('ix_solicitudes_restablecimiento_id'), table_name='solicitudes_restablecimiento')
    op.drop_table('solicitudes_restablecimiento')
