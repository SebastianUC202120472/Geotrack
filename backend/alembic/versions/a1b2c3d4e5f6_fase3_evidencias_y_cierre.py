"""Fase 3: columnas de evidencias (POD), motivo de fallo y cierre de ruta

Revision ID: a1b2c3d4e5f6
Revises: 428be2902cc3
Create Date: 2026-06-05 10:00:00.000000

Nota: las tablas 'rutas' y 'ruta_detalles' se crean en runtime via
Base.metadata.create_all (app/main.py). Esta migración añade únicamente las
columnas nuevas de la Fase 3 para entornos gestionados por Alembic.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '428be2902cc3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # CUS-28: marca temporal del cierre de la ruta
    op.add_column('rutas', sa.Column('fecha_fin', sa.DateTime(), nullable=True))

    # Fase 3.3: ejecución y evidencias
    op.add_column('ruta_detalles', sa.Column('motivo_fallo', sa.String(length=255), nullable=True))
    op.add_column('ruta_detalles', sa.Column('url_evidencia', sa.String(length=255), nullable=True))
    op.add_column('ruta_detalles', sa.Column('fecha_gestion', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('ruta_detalles', 'fecha_gestion')
    op.drop_column('ruta_detalles', 'url_evidencia')
    op.drop_column('ruta_detalles', 'motivo_fallo')
    op.drop_column('rutas', 'fecha_fin')
