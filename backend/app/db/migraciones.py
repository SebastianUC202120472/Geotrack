# Migraciones idempotentes del esquema. create_all solo crea tablas nuevas: no agrega
# columnas a tablas que ya existen en Postgres/Supabase, por eso las columnas nuevas
# se agregan aqui con ADD COLUMN IF NOT EXISTS (se pueden ejecutar en cada arranque).
from sqlalchemy import text

from app.db.database import Base

# Numero fijo del candado de Postgres que serializa el arranque cuando corren varios
# procesos del backend a la vez (evita que dos procesos creen la misma tabla).
_CANDADO_ARRANQUE = 7310214

# Sentencias en orden de aparicion. Agregar al final; nunca borrar ni reordenar.
SENTENCIAS = [
    # Acceso al portal de clientes corporativos.
    "ALTER TABLE clientes_corporativos ADD COLUMN IF NOT EXISTS codigo_acceso VARCHAR(30)",
    "ALTER TABLE clientes_corporativos ADD COLUMN IF NOT EXISTS clave_hash VARCHAR(255)",
    "ALTER TABLE clientes_corporativos ADD COLUMN IF NOT EXISTS correo_portal VARCHAR(150)",
    "ALTER TABLE clientes_corporativos ADD COLUMN IF NOT EXISTS acceso_activo BOOLEAN DEFAULT FALSE",
    "CREATE UNIQUE INDEX IF NOT EXISTS ix_clientes_codigo_acceso ON clientes_corporativos (codigo_acceso)",
    # Licencia de conducir del conductor (C03-03).
    "ALTER TABLE conductor_perfiles ADD COLUMN IF NOT EXISTS licencia_numero VARCHAR(20)",
    "ALTER TABLE conductor_perfiles ADD COLUMN IF NOT EXISTS licencia_vencimiento DATE",
    # Bloqueo progresivo de la verificacion del portal (C42-01).
    "ALTER TABLE verificaciones_portal ADD COLUMN IF NOT EXISTS bloqueos INTEGER DEFAULT 0",
    # Solicitudes de recojo: fecha pedida y visitas no realizadas (C11-04, C12-02).
    "ALTER TABLE solicitudes_recojo ADD COLUMN IF NOT EXISTS fecha_programada DATE",
    "ALTER TABLE solicitudes_recojo ADD COLUMN IF NOT EXISTS motivo_no_realizado VARCHAR(255)",
    "ALTER TABLE solicitudes_recojo ADD COLUMN IF NOT EXISTS intentos_no_realizados INTEGER DEFAULT 0",
    # Ubicacion de captura de las fotos del recojo (C13-01).
    "ALTER TABLE evidencias_recojo ADD COLUMN IF NOT EXISTS latitud_longitud_captura VARCHAR(60)",
]


def preparar_esquema(engine) -> None:
    """Crea las tablas que falten y aplica las migraciones en una sola transaccion. Recibe el engine."""
    with engine.begin() as conn:
        if conn.dialect.name == "postgresql":
            # Candado de transaccion: compatible con el pooler de Supabase en modo transaccion.
            conn.execute(text("SELECT pg_advisory_xact_lock(:n)"), {"n": _CANDADO_ARRANQUE})
        Base.metadata.create_all(bind=conn)
        for sentencia in SENTENCIAS:
            conn.execute(text(sentencia))
