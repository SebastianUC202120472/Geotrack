"""Recojos inbound (CUS-10/11/12): solicitudes_recojo + rutas.tipo

Revision ID: d0e1f2a3b4c5
Revises: c9d0e1f2a3b4
Create Date: 2026-06-21 12:00:00.000000

- solicitudes_recojo: órdenes de recojo del módulo Inbound.
- rutas.tipo: discriminador ENTREGA | RECOJO (server_default ENTREGA para BDs existentes).
En BDs nuevas todo lo crea Base.metadata.create_all; esta migración cubre las gestionadas por Alembic.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd0e1f2a3b4c5'
down_revision: Union[str, None] = 'c9d0e1f2a3b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('rutas', sa.Column('tipo', sa.String(length=20), server_default='ENTREGA', nullable=False))
    op.create_table(
        'solicitudes_recojo',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('codigo', sa.String(length=20), nullable=True),
        sa.Column('cliente_id', sa.Integer(), nullable=False),
        sa.Column('cliente_origen', sa.String(length=150), nullable=False),
        sa.Column('direccion_origen', sa.String(length=255), nullable=False),
        sa.Column('distrito', sa.String(length=100), nullable=True),
        sa.Column('latitud', sa.Float(), nullable=True),
        sa.Column('longitud', sa.Float(), nullable=True),
        sa.Column('volumen_estimado_m3', sa.Float(), nullable=True),
        sa.Column('contacto_origen', sa.String(length=100), nullable=True),
        sa.Column('referencia', sa.String(length=120), nullable=True),
        sa.Column('estado', sa.String(length=50), nullable=True),
        sa.Column('cantidad_declarada', sa.Integer(), nullable=True),
        sa.Column('url_guia', sa.String(length=255), nullable=True),
        sa.Column('ruta_id', sa.Integer(), nullable=True),
        sa.Column('secuencia', sa.Integer(), nullable=True),
        sa.Column('conversacion_id', sa.Integer(), nullable=True),
        sa.Column('fecha_creacion', sa.DateTime(), nullable=True),
        sa.Column('fecha_recojo', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['cliente_id'], ['clientes_corporativos.id']),
        sa.ForeignKeyConstraint(['ruta_id'], ['rutas.id']),
        sa.ForeignKeyConstraint(['conversacion_id'], ['correo_conversaciones.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_solicitudes_recojo_id'), 'solicitudes_recojo', ['id'], unique=False)
    op.create_index(op.f('ix_solicitudes_recojo_codigo'), 'solicitudes_recojo', ['codigo'], unique=True)
    op.create_index(op.f('ix_solicitudes_recojo_cliente_id'), 'solicitudes_recojo', ['cliente_id'], unique=False)
    op.create_index(op.f('ix_solicitudes_recojo_ruta_id'), 'solicitudes_recojo', ['ruta_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_solicitudes_recojo_ruta_id'), table_name='solicitudes_recojo')
    op.drop_index(op.f('ix_solicitudes_recojo_cliente_id'), table_name='solicitudes_recojo')
    op.drop_index(op.f('ix_solicitudes_recojo_codigo'), table_name='solicitudes_recojo')
    op.drop_index(op.f('ix_solicitudes_recojo_id'), table_name='solicitudes_recojo')
    op.drop_table('solicitudes_recojo')
    op.drop_column('rutas', 'tipo')
