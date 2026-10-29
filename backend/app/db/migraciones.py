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
    # Distrito que devuelve el geocodificador, guardado junto a la coordenada (C16-01).
    "ALTER TABLE geocodificaciones_cache ADD COLUMN IF NOT EXISTS distrito VARCHAR(100)",
    # Quien recibio la entrega (C26-02) y foto que respalda un reporte de falla (C29-01).
    "ALTER TABLE evidencias_entrega ADD COLUMN IF NOT EXISTS receptor_nombre VARCHAR(120)",
    "ALTER TABLE evidencias_entrega ADD COLUMN IF NOT EXISTS receptor_documento VARCHAR(12)",
    "ALTER TABLE reportes ADD COLUMN IF NOT EXISTS url_evidencia VARCHAR(255)",
    "ALTER TABLE reportes ADD COLUMN IF NOT EXISTS latitud_longitud_captura VARCHAR(60)",
    # Motivo obligatorio al cancelar un pedido (C31-02).
    "ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS motivo_cancelacion VARCHAR(255)",
    # Libro de Reclamaciones completo y su respuesta (C40-01, C41-02).
    "ALTER TABLE reclamos ADD COLUMN IF NOT EXISTS pedido_consumidor TEXT",
    "ALTER TABLE reclamos ADD COLUMN IF NOT EXISTS apoderado_nombre VARCHAR(150)",
    "ALTER TABLE reclamos ADD COLUMN IF NOT EXISTS apoderado_dni VARCHAR(20)",
    "ALTER TABLE reclamos ADD COLUMN IF NOT EXISTS respuesta TEXT",
    "ALTER TABLE reclamos ADD COLUMN IF NOT EXISTS respondido_en TIMESTAMP",
    "ALTER TABLE reclamos ADD COLUMN IF NOT EXISTS respondido_por INTEGER",
    # Historial de liquidaciones (C36-02).
    "ALTER TABLE liquidaciones ADD COLUMN IF NOT EXISTS cliente_nombre VARCHAR(150)",
    "ALTER TABLE liquidaciones ADD COLUMN IF NOT EXISTS total_pedidos INTEGER",
    # Retencion de datos del destinatario (EX-04).
    "ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS datos_retirados_en TIMESTAMP",
    # Consumo de bateria del celular en la jornada (EX-15).
    "ALTER TABLE rutas ADD COLUMN IF NOT EXISTS bateria_inicio DOUBLE PRECISION",
    "ALTER TABLE rutas ADD COLUMN IF NOT EXISTS bateria_inicio_en TIMESTAMP",
    "ALTER TABLE rutas ADD COLUMN IF NOT EXISTS bateria_fin DOUBLE PRECISION",
    "ALTER TABLE rutas ADD COLUMN IF NOT EXISTS bateria_fin_en TIMESTAMP",
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
