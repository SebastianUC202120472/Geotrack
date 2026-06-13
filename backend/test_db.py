from app.db.database import engine, Base
from app.models.usuario import Usuario

print("Intentando crear tablas...")
try:
    Base.metadata.create_all(bind=engine)
    print("¡Éxito! Base.metadata.create_all() se ejecutó sin errores.")
except Exception as e:
    print(f"Error crítico al crear tablas: {e}")