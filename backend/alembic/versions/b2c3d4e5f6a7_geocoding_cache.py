"""Caché de geocodificación (tabla geocodificaciones_cache)

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-29 19:00:00.000000

Guarda la coordenada de cada dirección ya resuelta para no volver a llamar al proveedor
(Google) por la misma dirección. En BDs nuevas la crea create_all (app/main.py); esta
migración cubre los entornos ya gestionados por Alembic.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "geocodificaciones_cache",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("direccion_normalizada", sa.String(length=500), nullable=False),
        sa.Column("latitud", sa.Float(), nullable=False),
        sa.Column("longitud", sa.Float(), nullable=False),
        sa.Column("proveedor", sa.String(length=20), nullable=True),
        sa.Column("creado_en", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_geocodificaciones_cache_id", "geocodificaciones_cache", ["id"])
    op.create_index(
        "ix_geocodificaciones_cache_direccion_normalizada",
        "geocodificaciones_cache",
        ["direccion_normalizada"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_geocodificaciones_cache_direccion_normalizada", table_name="geocodificaciones_cache")
    op.drop_index("ix_geocodificaciones_cache_id", table_name="geocodificaciones_cache")
    op.drop_table("geocodificaciones_cache")
