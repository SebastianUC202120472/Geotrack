# app/models/__init__.py
# Importamos TODOS los modelos aquí para que SQLAlchemy registre cada tabla en
# Base.metadata. Esto lo aprovechan:
#   - create_all (app/main.py) para crear las tablas al arrancar.
#   - Alembic (alembic/env.py) para detectar cambios y generar migraciones.
from .usuario import Usuario
from .cliente import ClienteCorporativo
from .vehiculo import Vehiculo
from .pedido import Pedido
from .ruta import Ruta, RutaDetalle
from .historial import HistorialPedido
from .correo import Conversacion, MensajeCorreo, MensajeAdjunto
from .conductor import PerfilConductor
