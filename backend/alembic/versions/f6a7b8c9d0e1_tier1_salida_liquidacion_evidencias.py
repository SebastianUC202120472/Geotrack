"""TIER 1: salida de ruta, liquidaciones y evidencias de entrega

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-06-20 12:00:00.000000

Cambios:
  - rutas.fecha_salida: momento de salida del almacén (CUS-23), base para calcular
    las horas trabajadas al cerrar la ruta (CUS-28).
  - tabla liquidaciones: registro del reporte de liquidación por cliente (CUS-36).
  - tabla evidencias_entrega: prueba de entrega (POD) como registro propio (CUS-26).

Nota: en BDs nuevas estas estructuras las crea Base.metadata.create_all (app/main.py);
esta migración cubre los entornos ya gestionados por Alembic.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # CUS-23/28: momento de salida del almacén en cada ruta.
    op.add_column('rutas', sa.Column('fecha_salida', sa.DateTime(), nullable=True))

    # CUS-36: liquidaciones generadas por cliente.
    op.create_table(
        'liquidaciones',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cliente_id', sa.Integer(), nullable=True),
        sa.Column('periodo_inicio', sa.Date(), nullable=True),
        sa.Column('periodo_fin', sa.Date(), nullable=True),
        sa.Column('url_documento', sa.String(length=255), nullable=False),
        sa.Column('fecha_generacion', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['cliente_id'], ['clientes_corporativos.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_liquidaciones_id'), 'liquidaciones', ['id'], unique=False)
    op.create_index(op.f('ix_liquidaciones_cliente_id'), 'liquidaciones', ['cliente_id'], unique=False)

    # CUS-26: evidencias de entrega (POD) como registro propio.
    op.create_table(
        'evidencias_entrega',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pedido_id', sa.Integer(), nullable=False),
        sa.Column('url_foto', sa.String(length=255), nullable=True),
        sa.Column('url_firma', sa.String(length=255), nullable=True),
        sa.Column('latitud_longitud_captura', sa.String(length=60), nullable=True),
        sa.Column('fecha_hora', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['pedido_id'], ['pedidos.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_evidencias_entrega_id'), 'evidencias_entrega', ['id'], unique=False)
    op.create_index(op.f('ix_evidencias_entrega_pedido_id'), 'evidencias_entrega', ['pedido_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_evidencias_entrega_pedido_id'), table_name='evidencias_entrega')
    op.drop_index(op.f('ix_evidencias_entrega_id'), table_name='evidencias_entrega')
    op.drop_table('evidencias_entrega')

    op.drop_index(op.f('ix_liquidaciones_cliente_id'), table_name='liquidaciones')
    op.drop_index(op.f('ix_liquidaciones_id'), table_name='liquidaciones')
    op.drop_table('liquidaciones')

    op.drop_column('rutas', 'fecha_salida')
