# app/db/database.py
# ============================================================================
# CAPA: DB (conexión a la base de datos) — Clean Architecture
# ----------------------------------------------------------------------------
# ¿QUÉ HACE?  Configura la conexión a PostgreSQL y entrega "sesiones" para
#             que el resto del código pueda leer/escribir en la BD.
# ¿CÓMO?      - 'engine': el motor que conecta con PostgreSQL.
#             - 'SessionLocal': fábrica de sesiones (una por petición).
#             - 'Base': clase madre de la que heredan TODOS los modelos.
#             - 'get_db()': dependencia que abre una sesión y la cierra sola.
# ¿CON QUÉ SE CONECTA?
#   - models/*.py heredan de 'Base'.
#   - Todos los endpoints piden 'get_db' con Depends() para obtener 'db'.
# ============================================================================
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

# URL de conexión a PostgreSQL. Ahora viene de la configuración central
# (variable de entorno DATABASE_URL), NO escrita en el código.
# El host 'db' es el NOMBRE DEL SERVICIO en docker-compose.yml (red interna de Docker).
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# Motor: traduce el código Python a SQL y mantiene la conexión.
engine = create_engine(SQLALCHEMY_DATABASE_URL)

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
