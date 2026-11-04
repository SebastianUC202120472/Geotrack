# Conexion a la base de datos PROPIA del asistente. Sus tablas viven en un esquema
# aparte ("asistente"): el modulo nunca lee ni escribe las tablas del nucleo.
from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

_opciones = {"pool_pre_ping": True}
if settings.ASISTENTE_DATABASE_URL.startswith("sqlite"):
    _opciones = {"connect_args": {"check_same_thread": False}}

engine = create_engine(settings.ASISTENTE_DATABASE_URL, **_opciones)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base(metadata=MetaData(schema=settings.esquema_db))


def preparar_tablas() -> None:
    """Crea el esquema y las tablas propias si no existen. Sin input."""
    from app import models  # noqa: F401  (registra los modelos en Base)

    if settings.esquema_db and engine.dialect.name == "postgresql":
        with engine.begin() as conexion:
            conexion.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{settings.esquema_db}"'))
    Base.metadata.create_all(bind=engine)


def get_db():
    """Entrega una sesion de BD por peticion y la cierra al terminar. Sin input."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
