from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings
from app.core.registro import obtener_logger

_log = obtener_logger("database")

_opciones = {
    "pool_pre_ping": True,
    "pool_size": 2,
    "max_overflow": 2,
}

if settings.AUDITORIA_DATABASE_URL.startswith("sqlite"):
    _opciones = {
        "connect_args": {"check_same_thread": False},
        "execution_options": {"schema_translate_map": {settings.AUDITORIA_DB_SCHEMA: None}},
    }


def url_con_driver(url: str) -> str:
    """Asegura el driver psycopg2 para SQLAlchemy en postgresql://."""
    for prefijo in ("postgresql://", "postgres://"):
        if url.startswith(prefijo):
            return "postgresql+psycopg2://" + url[len(prefijo):]
    return url


engine = create_engine(url_con_driver(settings.AUDITORIA_DATABASE_URL), **_opciones)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# Si es SQLite, no se usa schema porque SQLite no soporta esquemas de esa forma
_esquema = settings.AUDITORIA_DB_SCHEMA if not settings.AUDITORIA_DATABASE_URL.startswith("sqlite") else None
Base = declarative_base(metadata=MetaData(schema=_esquema))


def preparar_tablas() -> None:
    """Crea el esquema y las tablas propias de auditoría si no existen."""
    from app import models  # noqa: F401

    if _esquema and engine.dialect.name == "postgresql":
        with engine.begin() as conexion:
            _log.info("Verificando existencia del esquema '%s'...", _esquema)
            conexion.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{_esquema}"'))

    Base.metadata.create_all(bind=engine)
    _log.info("Tablas de auditoría inicializadas correctamente.")


def get_db():
    """Generador de sesión de BD por petición."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
