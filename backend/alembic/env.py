# alembic/env.py
# ============================================================================
# Configuración de Alembic (control de versiones de la base de datos).
# ----------------------------------------------------------------------------
# ¿QUÉ HACE?  Le dice a Alembic CÓMO conectarse y QUÉ tablas debe vigilar para
#             generar y aplicar migraciones (ALTER/CREATE de la BD).
# ¿CON QUÉ SE CONECTA?
#   - app/db/database.py -> de ahí toma 'Base' (los metadatos de las tablas).
#   - app/models/*       -> los importa para que TODAS las tablas se registren.
#   - alembic.ini        -> de ahí toma la URL de conexión (sqlalchemy.url).
# ============================================================================
import sys
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# 1) Permitir importar el paquete 'app' desde la raíz del proyecto.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# 2) Importar Base y TODOS los modelos (importar el paquete registra sus tablas).
from app.db.database import Base
import app.models  # noqa: F401  (registra Usuario, Pedido, Ruta, RutaDetalle)

# Objeto de configuración de Alembic (lee alembic.ini).
config = context.config

# Configuración de logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 3) Metadatos que Alembic compara contra la BD para detectar cambios.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Modo 'offline': genera el SQL sin conectarse realmente a la BD."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Modo 'online': se conecta a la BD y aplica las migraciones."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


# Punto de entrada: ejecuta el modo correcto UNA sola vez.
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
