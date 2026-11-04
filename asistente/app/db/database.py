# Conexion a la base de datos PROPIA del asistente. Sus tablas viven en un esquema
# aparte ("asistente"): el modulo nunca lee ni escribe las tablas del nucleo.
from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

# Pocas conexiones: el asistente solo guarda historial y auditoria, y el pooler de Supabase
# en modo sesion admite 15 clientes en total (compartidos con el backend y el equipo).
_opciones = {"pool_pre_ping": True, "pool_size": 2, "max_overflow": 3}
if settings.ASISTENTE_DATABASE_URL.startswith("sqlite"):
    _opciones = {"connect_args": {"check_same_thread": False}}


def url_con_driver(url: str) -> str:
    """Fija el driver psycopg2 en las URL "postgresql://" (desde SQLAlchemy 2.1 usan psycopg 3,
    que no esta instalado). Recibe la URL de la BD."""
    for prefijo in ("postgresql://", "postgres://"):
        if url.startswith(prefijo):
            return "postgresql+psycopg2://" + url[len(prefijo):]
    return url


engine = create_engine(url_con_driver(settings.ASISTENTE_DATABASE_URL), **_opciones)
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
