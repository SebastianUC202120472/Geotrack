"""Capacidad en cajas (CUS-08) y tabla de parámetros del sistema (CUS-06)

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-06-20 14:00:00.000000

- vehiculos.capacidad_cajas: cuántas cajas soporta el vehículo (la tesis lo pide así;
  se suma a la capacidad volumétrica en m³ que ya existía).
- parametros_sistema: catálogos administrables del sistema (CUS-06). Por ahora se usa
  para los motivos de rechazo (categoria='motivo_rechazo').

En BDs nuevas todo lo crea Base.metadata.create_all (app/main.py); esta migración
cubre los entornos ya gestionados por Alembic.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b8c9d0e1f2a3'
down_revision: Union[str, None] = 'a7b8c9d0e1f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('vehiculos', sa.Column('capacidad_cajas', sa.Integer(), nullable=True))

    op.create_table(
        'parametros_sistema',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('categoria', sa.String(length=50), nullable=False),
        sa.Column('clave', sa.String(length=120), nullable=False),
        sa.Column('valor_json', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_parametros_sistema_id'), 'parametros_sistema', ['id'], unique=False)
    op.create_index(op.f('ix_parametros_sistema_categoria'), 'parametros_sistema', ['categoria'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_parametros_sistema_categoria'), table_name='parametros_sistema')
    op.drop_index(op.f('ix_parametros_sistema_id'), table_name='parametros_sistema')
    op.drop_table('parametros_sistema')
    op.drop_column('vehiculos', 'capacidad_cajas')
