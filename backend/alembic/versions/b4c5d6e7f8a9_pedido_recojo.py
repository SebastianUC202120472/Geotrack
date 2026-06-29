# b4c5d6e7f8a9_pedido_recojo.py
# Añade provenance de recojo y soporte al estado POR_RECOGER en la tabla pedidos.
"""pedido: provenance de recojo y estado POR_RECOGER

Revision ID: b4c5d6e7f8a9
Revises: a3b4c5d6e7f8
Create Date: 2026-06-28 00:00:00.000000
"""
from typing import Union
from alembic import op
import sqlalchemy as sa

revision: str = 'b4c5d6e7f8a9'
down_revision: Union[str, None] = 'a3b4c5d6e7f8'
branch_labels = None
depends_on = None


def upgrade():
    # Añade la FK al recojo origen, índice y columnas de validación en almacén
    op.add_column("pedidos", sa.Column("recojo_id", sa.Integer(), nullable=True))
    op.create_index("ix_pedidos_recojo_id", "pedidos", ["recojo_id"])
    op.create_foreign_key("fk_pedidos_recojo", "pedidos", "solicitudes_recojo", ["recojo_id"], ["id"])
    op.add_column("pedidos", sa.Column("validado_en", sa.DateTime(), nullable=True))
    op.add_column("pedidos", sa.Column("validado_por", sa.Integer(), nullable=True))


def downgrade():
    # Elimina en orden inverso: FK, índice y columnas
    op.drop_constraint("fk_pedidos_recojo", "pedidos", type_="foreignkey")
    op.drop_index("ix_pedidos_recojo_id", "pedidos")
    for c in ("validado_por", "validado_en", "recojo_id"):
        op.drop_column("pedidos", c)
