"""Elimina las tablas muertas paquetes_esperados y escaneos_desconocidos

Revision ID: a1b2c3d4e5f6
Revises: e2f3a4b5c6d7
Create Date: 2026-06-29 18:00:00.000000

Motivo: estas dos tablas (la "trama" de paquetes esperados y los escaneos
sobrantes) eran del flujo de almacén CON escáner QR (CUS-14). Al adoptar el
ingreso manual ("almacén sin escaneo"), ningún servicio, repositorio ni endpoint
las lee o escribe: quedan vacías y solo confunden el modelo. Se eliminan junto al
modelo SQLAlchemy y al endpoint conductor /almacen/validar-qr que lo acompañaba.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'e2f3a4b5c6d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Tablas vacías y sin uso: se borran si existen (idempotente entre entornos).
    op.execute("DROP TABLE IF EXISTS escaneos_desconocidos")
    op.execute("DROP TABLE IF EXISTS paquetes_esperados")


def downgrade() -> None:
    # Recrea las estructuras mínimas por si se revierte (sin datos que restaurar).
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS paquetes_esperados (
            id SERIAL PRIMARY KEY,
            codigo VARCHAR(50) NOT NULL,
            recojo_id INTEGER NOT NULL REFERENCES solicitudes_recojo(id),
            estado VARCHAR(20) DEFAULT 'ESPERADO',
            escaneado_en TIMESTAMP NULL,
            escaneado_por INTEGER NULL,
            creado_en TIMESTAMP NULL
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS escaneos_desconocidos (
            id SERIAL PRIMARY KEY,
            recojo_id INTEGER NOT NULL REFERENCES solicitudes_recojo(id),
            codigo VARCHAR(50) NOT NULL,
            escaneado_en TIMESTAMP NULL,
            escaneado_por INTEGER NULL
        )
        """
    )
