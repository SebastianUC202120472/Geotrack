# Prepara la demostracion de la sustentacion en un solo paso:
#  1. Vacia los datos operativos y siembra el portal de clientes con pedidos de HOY de
#     Ripley, Oechsle, Promart y Plaza Vea (entregados con foto, en ruta, por salir,
#     reprogramados y observados), con sus rutas e historial.
#  2. Deja a Saga Falabella SIN pedidos y su correo de solicitud (6 pedidos) pendiente en la
#     Bandeja, para recorrer en vivo el flujo completo: Bandeja -> almacen -> zonas -> rutas
#     -> app del conductor -> portal.
# Conserva usuarios, conductores, vehiculos y parametros. Juan (juan@prueba.com) queda libre.
# Sin --si solo explica lo que haria. Correr dentro del contenedor backend:
#   docker exec geotrack-backend-1 python scripts/preparar_demo.py --si
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text  # noqa: E402

from app.db.database import SessionLocal  # noqa: E402

import reset_demo  # noqa: E402
import seed_portal_demo  # noqa: E402

# Empresa que se deja sin pedidos para hacer el flujo en vivo desde la Bandeja.
EMPRESA_EN_VIVO = "FALABELLA"


def cerrar_transacciones_colgadas() -> int:
    """Cierra las conexiones de este usuario que quedaron "idle in transaction" mas de 60 s (p. ej.
    un reinicio anterior que se corto): bloquean las tablas y el vaciado moriria por timeout.
    Sin input. Devuelve cuantas cerro."""
    db = SessionLocal()
    try:
        pids = [fila[0] for fila in db.execute(text(
            "SELECT pid FROM pg_stat_activity WHERE datname = current_database() "
            "AND usename = current_user AND pid <> pg_backend_pid() "
            "AND state LIKE 'idle in transaction%' AND now() - state_change > interval '60 seconds'"
        )).fetchall()]
        for pid in pids:
            db.execute(text("SELECT pg_terminate_backend(:pid)"), {"pid": pid})
        db.commit()
        return len(pids)
    finally:
        db.close()


def main():
    """Siembra el portal (sin la empresa en vivo) y deja su correo en la Bandeja. Sin input."""
    if "--si" not in sys.argv:
        print("Simulacion: no se toco nada. Con --si se borran los datos operativos, se siembran")
        print("200 pedidos de hoy (4 empresas) y se deja el correo de Saga Falabella en la Bandeja.")
        return
    cerradas = cerrar_transacciones_colgadas()
    if cerradas:
        print(f"Se cerraron {cerradas} conexion(es) colgada(s) de un intento anterior.")
    seed_portal_demo._sembrar(excluir={EMPRESA_EN_VIVO})
    db = SessionLocal()
    try:
        conv_id = reset_demo.sembrar_correo_demo(db)
        db.commit()
        print(f"Correo de {reset_demo.NOMBRE_CLIENTE} pendiente en la Bandeja (conversacion {conv_id}).")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
