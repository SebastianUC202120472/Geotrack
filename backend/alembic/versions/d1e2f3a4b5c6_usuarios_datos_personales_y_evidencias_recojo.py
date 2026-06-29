# d1e2f3a4b5c6_usuarios_datos_personales_y_evidencias_recojo.py
# Datos personales del personal de panel (Modo Perfil) + tabla de evidencias de recojo
# (varias fotos por recepción). Para entornos gestionados por Alembic; en el arranque por
# defecto, create_all ya crea la tabla nueva y, en BD existentes, las columnas se agregaron
# por ALTER (ver despliegue). Esta migración deja el esquema reproducible vía 'alembic upgrade'.
"""usuarios: datos personales + tabla evidencias_recojo

Revision ID: d1e2f3a4b5c6
Revises: c5d6e7f8a9b0
Create Date: 2026-06-29 00:00:00.000000
"""
from typing import Union

from alembic import op
import sqlalchemy as sa

revision: str = "d1e2f3a4b5c6"
down_revision: Union[str, None] = "c5d6e7f8a9b0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Agrega los datos personales a 'usuarios' y crea 'evidencias_recojo'."""
    op.add_column("usuarios", sa.Column("nombre", sa.String(120), nullable=True))
    op.add_column("usuarios", sa.Column("dni", sa.String(15), nullable=True))
    op.add_column("usuarios", sa.Column("telefono", sa.String(20), nullable=True))
    op.add_column("usuarios", sa.Column("cargo", sa.String(80), nullable=True))

    op.create_table(
        "evidencias_recojo",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("recojo_id", sa.Integer, sa.ForeignKey("solicitudes_recojo.id"), nullable=False),
        sa.Column("url_foto", sa.String(255), nullable=False),
        sa.Column("secuencia", sa.Integer),
        sa.Column("creado_en", sa.DateTime),
    )
    op.create_index("ix_evidencias_recojo_recojo_id", "evidencias_recojo", ["recojo_id"])


def downgrade() -> None:
    """Revierte: elimina la tabla de evidencias y las columnas personales de 'usuarios'."""
    op.drop_index("ix_evidencias_recojo_recojo_id", "evidencias_recojo")
    op.drop_table("evidencias_recojo")
    op.drop_column("usuarios", "cargo")
    op.drop_column("usuarios", "telefono")
    op.drop_column("usuarios", "dni")
    op.drop_column("usuarios", "nombre")
