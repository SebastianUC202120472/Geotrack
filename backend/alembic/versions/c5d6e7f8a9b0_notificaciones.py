# c5d6e7f8a9b0_notificaciones.py
# Crea la tabla `notificaciones` para el historial de avisos del panel admin.
"""notificaciones: tabla con historial y estado de lectura

Revision ID: c5d6e7f8a9b0
Revises: b4c5d6e7f8a9
Create Date: 2026-06-28 00:00:00.000000
"""
from typing import Union

from alembic import op
import sqlalchemy as sa

revision: str = "c5d6e7f8a9b0"
down_revision: Union[str, None] = "b4c5d6e7f8a9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Crea la tabla notificaciones con índice en creado_en."""
    op.create_table(
        "notificaciones",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("tipo", sa.String(30), nullable=False),
        sa.Column("titulo", sa.String(120), nullable=False),
        sa.Column("mensaje", sa.String(255)),
        sa.Column("ruta", sa.String(120)),
        sa.Column("entidad_id", sa.Integer),
        sa.Column("creado_en", sa.DateTime),
        sa.Column("visto_en", sa.DateTime),
    )
    op.create_index("ix_notificaciones_creado_en", "notificaciones", ["creado_en"])


def downgrade() -> None:
    """Elimina la tabla notificaciones."""
    op.drop_index("ix_notificaciones_creado_en", "notificaciones")
    op.drop_table("notificaciones")
