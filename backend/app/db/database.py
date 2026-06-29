# app/db/database.py
# Configura la conexión a PostgreSQL y entrega "sesiones" para que el resto del código pueda leer/escribir en la BD.
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

# URL de conexión a PostgreSQL. Ahora viene de la configuración central
# (variable de entorno DATABASE_URL), NO escrita en el código.
# El host 'db' es el NOMBRE DEL SERVICIO en docker-compose.yml (red interna de Docker).
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# Motor: traduce el código Python a SQL y mantiene la conexión.
# pool_pre_ping: valida la conexión con un ping antes de usarla; el Session pooler de
#   Supabase cierra las conexiones ociosas y sin esto se obtienen fallos intermitentes
#   ("server closed the connection") que un reintento arreglaba.
# pool_recycle: recicla la conexión a los 5 min para no reutilizar una que el pooler ya cerró.
# pool_size/max_overflow: cota razonable para una BD remota compartida.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=5,
    max_overflow=10,
)

# Fábrica de sesiones. autocommit/autoflush en False = control manual y seguro.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Clase base: cada modelo (tabla) hereda de aquí para que SQLAlchemy lo registre.
Base = declarative_base()


def get_db():
    """
    Dependencia de FastAPI: abre una sesión de BD para la petición y garantiza
    que se cierre al terminar (incluso si hay un error). Se usa así en los
    endpoints:  db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db          # entrega la sesión al endpoint
    finally:
        db.close()        # la cierra siempre al finalizar
