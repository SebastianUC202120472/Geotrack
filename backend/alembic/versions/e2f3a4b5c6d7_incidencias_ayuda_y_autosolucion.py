# e2f3a4b5c6d7_incidencias_ayuda_y_autosolucion.py
# Auxilio mecánico: el conductor puede marcar que resuelve solo, y el admin "manda ayuda"
# (tipo + nota) sin resolver la incidencia. Para entornos gestionados por Alembic; en el
# arranque por defecto create_all crea la tabla nueva pero NO agrega columnas a existentes,
# así que en BD vivas estas columnas se aplican también por ALTER (ver despliegue).
"""incidencias: puede_solucionar_solo + sello de ayuda enviada

Revision ID: e2f3a4b5c6d7
Revises: d1e2f3a4b5c6
Create Date: 2026-06-29 12:00:00.000000
"""
from typing import Union

from alembic import op
import sqlalchemy as sa

revision: str = "e2f3a4b5c6d7"
down_revision: Union[str, None] = "d1e2f3a4b5c6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Agrega a 'incidencias' el flag de auto-solución y el sello de ayuda enviada."""
    op.add_column("incidencias", sa.Column("puede_solucionar_solo", sa.Boolean(), nullable=True))
    op.add_column("incidencias", sa.Column("ayuda_enviada_en", sa.DateTime(), nullable=True))
    op.add_column("incidencias", sa.Column("ayuda_enviada_por", sa.Integer(), nullable=True))
    op.add_column("incidencias", sa.Column("ayuda_detalle", sa.String(255), nullable=True))


def downgrade() -> None:
    """Revierte las columnas de ayuda/auto-solución."""
    op.drop_column("incidencias", "ayuda_detalle")
    op.drop_column("incidencias", "ayuda_enviada_por")
    op.drop_column("incidencias", "ayuda_enviada_en")
    op.drop_column("incidencias", "puede_solucionar_solo")
