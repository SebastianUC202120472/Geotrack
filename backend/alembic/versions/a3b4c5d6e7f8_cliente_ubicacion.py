"""Cliente gana campos de ubicación de recojo geocodificada (CUS-16)

Revision ID: a3b4c5d6e7f8
Revises: f2a3b4c5d6e7
Create Date: 2026-06-28 00:00:00.000000

Añade direccion_origen, distrito, latitud y longitud a clientes_corporativos
para almacenar el punto de recojo del cliente y sus coordenadas.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a3b4c5d6e7f8'
down_revision: Union[str, None] = 'f2a3b4c5d6e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("clientes_corporativos", sa.Column("direccion_origen", sa.String(255), nullable=True))
    op.add_column("clientes_corporativos", sa.Column("distrito", sa.String(100), nullable=True))
    op.add_column("clientes_corporativos", sa.Column("latitud", sa.Float(), nullable=True))
    op.add_column("clientes_corporativos", sa.Column("longitud", sa.Float(), nullable=True))


def downgrade() -> None:
    for c in ("longitud", "latitud", "distrito", "direccion_origen"):
        op.drop_column("clientes_corporativos", c)
