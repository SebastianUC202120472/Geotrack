"""Fase 4 (Nivel 1): clientes_corporativos, datos de destinatario e historial_pedidos

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-06 12:00:00.000000

Alinea el modelo con la propuesta de tesis: el cliente pasa a ser una entidad
propia, el pedido guarda los datos del destinatario, y se añade la tabla de
trazabilidad de eventos (historial_pedidos).

Nota: las tablas se crean en runtime con create_all (app/main.py); esta
migración es para entornos gestionados por Alembic.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) Tabla de clientes corporativos (la empresa que envía).
    op.create_table(
        'clientes_corporativos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('razon_social', sa.String(length=150), nullable=False),
        sa.Column('identificador_unico', sa.String(length=20), nullable=True),
        sa.Column('contacto', sa.String(length=100), nullable=True),
        sa.Column('creado_en', sa.DateTime(), nullable=True),
        sa.Column('eliminado_en', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_clientes_corporativos_id'), 'clientes_corporativos', ['id'])
    op.create_index(op.f('ix_clientes_corporativos_identificador_unico'),
                    'clientes_corporativos', ['identificador_unico'], unique=True)

    # 2) Pedido: enlace al cliente + datos del destinatario.
    op.add_column('pedidos', sa.Column('cliente_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_pedidos_cliente_id'), 'pedidos', ['cliente_id'])
    op.create_foreign_key('fk_pedidos_cliente', 'pedidos', 'clientes_corporativos', ['cliente_id'], ['id'])
    op.add_column('pedidos', sa.Column('nombre_destinatario', sa.String(length=120), nullable=True))
    op.add_column('pedidos', sa.Column('telefono_destinatario', sa.String(length=30), nullable=True))
    op.add_column('pedidos', sa.Column('dni_destinatario', sa.String(length=20), nullable=True))

    # 3) Tabla de trazabilidad de eventos.
    op.create_table(
        'historial_pedidos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pedido_id', sa.Integer(), nullable=False),
        sa.Column('estado_anterior', sa.String(length=50), nullable=True),
        sa.Column('estado_nuevo', sa.String(length=50), nullable=False),
        sa.Column('usuario_id', sa.Integer(), nullable=True),
        sa.Column('fecha_utc', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['pedido_id'], ['pedidos.id']),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_historial_pedidos_id'), 'historial_pedidos', ['id'])
    op.create_index(op.f('ix_historial_pedidos_pedido_id'), 'historial_pedidos', ['pedido_id'])


def downgrade() -> None:
    op.drop_table('historial_pedidos')
    op.drop_constraint('fk_pedidos_cliente', 'pedidos', type_='foreignkey')
    op.drop_index(op.f('ix_pedidos_cliente_id'), table_name='pedidos')
    op.drop_column('pedidos', 'dni_destinatario')
    op.drop_column('pedidos', 'telefono_destinatario')
    op.drop_column('pedidos', 'nombre_destinatario')
    op.drop_column('pedidos', 'cliente_id')
    op.drop_table('clientes_corporativos')
