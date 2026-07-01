from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# pool_pre_ping y pool_recycle evitan fallos con el pooler de Supabase que cierra conexiones ociosas.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=5,
    max_overflow=10,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependencia FastAPI: entrega una sesion de BD y la cierra al terminar. Recibe nada."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
