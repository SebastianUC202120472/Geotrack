"""Foto del conductor: columna foto_url en conductor_perfiles

Revision ID: e5f6a7b8c9d0
Revises: e4f5a6b7c8d9
Create Date: 2026-06-20 10:00:00.000000

Nota: en BDs nuevas la columna la crea Base.metadata.create_all (app/main.py);
esta migración cubre los entornos ya gestionados por Alembic.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'e4f5a6b7c8d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('conductor_perfiles', sa.Column('foto_url', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('conductor_perfiles', 'foto_url')
