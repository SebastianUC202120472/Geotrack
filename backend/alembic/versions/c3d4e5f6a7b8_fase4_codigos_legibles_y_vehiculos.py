"""Fase 4: códigos legibles (PD/RT/HP...), tabla vehiculos y referencia_externa

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-06-06 14:00:00.000000

Hace la BD trazable a simple vista: cada tabla gana una columna 'codigo'
legible (CL/PD/RT/RD/HP/VE-001, usuarios AD/CO-001). En pedidos, 'codigo'
(PD-001) reemplaza a 'numero_tracking' como identificador/QR, y el id del
Excel se guarda en 'referencia_externa'. Se añade la tabla 'vehiculos'.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _add_codigo(tabla: str) -> None:
    """Añade la columna 'codigo' (única) a una tabla."""
    op.add_column(tabla, sa.Column('codigo', sa.String(length=20), nullable=True))
    op.create_index(op.f(f'ix_{tabla}_codigo'), tabla, ['codigo'], unique=True)


def _drop_codigo(tabla: str) -> None:
    op.drop_index(op.f(f'ix_{tabla}_codigo'), table_name=tabla)
    op.drop_column(tabla, 'codigo')


def upgrade() -> None:
    # 1) Tabla de vehículos.
    op.create_table(
        'vehiculos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('codigo', sa.String(length=20), nullable=True),
        sa.Column('placa', sa.String(length=20), nullable=False),
        sa.Column('marca', sa.String(length=60), nullable=True),
        sa.Column('capacidad_volumetrica', sa.Float(), nullable=True),
        sa.Column('estado', sa.String(length=30), nullable=True),
        sa.Column('conductor_id', sa.Integer(), nullable=True),
        sa.Column('creado_en', sa.DateTime(), nullable=True),
        sa.Column('eliminado_en', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['conductor_id'], ['usuarios.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_vehiculos_id'), 'vehiculos', ['id'])
    op.create_index(op.f('ix_vehiculos_codigo'), 'vehiculos', ['codigo'], unique=True)
    op.create_index(op.f('ix_vehiculos_placa'), 'vehiculos', ['placa'], unique=True)
    op.create_index(op.f('ix_vehiculos_conductor_id'), 'vehiculos', ['conductor_id'])

    # 2) Columna 'codigo' legible en cada tabla.
    for tabla in ('usuarios', 'clientes_corporativos', 'rutas', 'ruta_detalles', 'historial_pedidos'):
        _add_codigo(tabla)

    # 3) Pedidos: codigo (PD-001) + referencia_externa; se elimina numero_tracking.
    _add_codigo('pedidos')
    op.add_column('pedidos', sa.Column('referencia_externa', sa.String(length=50), nullable=True))
    op.create_index(op.f('ix_pedidos_referencia_externa'), 'pedidos', ['referencia_externa'])
    op.drop_index('ix_pedidos_numero_tracking', table_name='pedidos')
    op.drop_column('pedidos', 'numero_tracking')


def downgrade() -> None:
    op.add_column('pedidos', sa.Column('numero_tracking', sa.String(length=50), nullable=True))
    op.create_index('ix_pedidos_numero_tracking', 'pedidos', ['numero_tracking'], unique=True)
    op.drop_index(op.f('ix_pedidos_referencia_externa'), table_name='pedidos')
    op.drop_column('pedidos', 'referencia_externa')
    _drop_codigo('pedidos')

    for tabla in ('historial_pedidos', 'ruta_detalles', 'rutas', 'clientes_corporativos', 'usuarios'):
        _drop_codigo(tabla)

    op.drop_table('vehiculos')
