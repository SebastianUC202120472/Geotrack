"""Retorno a almacén (CUS-32): ruta_detalles.retornado_en / retornado_por

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6
Create Date: 2026-06-21 16:00:00.000000

Logística inversa: marca de retorno físico de los paquetes FALLIDO. No cambia el
estado del pedido (sigue FALLIDO para CUS-31). En BD nueva las crea create_all.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f2a3b4c5d6e7'
down_revision: Union[str, None] = 'e1f2a3b4c5d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('ruta_detalles', sa.Column('retornado_en', sa.DateTime(), nullable=True))
    op.add_column('ruta_detalles', sa.Column('retornado_por', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('ruta_detalles', 'retornado_por')
    op.drop_column('ruta_detalles', 'retornado_en')
