# Reinicia la demostracion desde cero: borra los datos operativos (pedidos, recojos, rutas,
# historial, evidencias, reportes, notificaciones, ubicaciones...) con la numeracion de nuevo
# en 1, y deja en la Bandeja el correo de Saga Falabella con su Excel de 6 pedidos, pendiente.
# CONSERVA usuarios, conductores, vehiculos, clientes, parametros, el resto de la Bandeja y la
# cache de direcciones. Sin --si solo muestra lo que borraria (no toca nada).
# Correr dentro del contenedor backend:  python scripts/reset_demo.py --si
import os
import sys
from datetime import datetime

# Asegura que /app (raiz del backend) este en el path para poder importar el paquete app.*
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text  # noqa: E402

from app.db.database import SessionLocal  # noqa: E402
from app.models.correo import Conversacion, MensajeCorreo, MensajeAdjunto  # noqa: E402

TABLAS_OPERATIVAS = (
    "pedidos", "ruta_detalles", "rutas", "solicitudes_recojo", "reportes", "incidencias",
    "notificaciones", "historial_pedidos", "evidencias_entrega", "evidencias_recojo",
    "liquidaciones", "ubicaciones_conductor", "verificaciones_portal",
)

EXCEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "solicitud_recojo_falabella_demo.xlsx")
EMAIL_CLIENTE = "despachos@sagafalabella.com.pe"
NOMBRE_CLIENTE = "Saga Falabella S.A."  # igual a la razon social: la Bandeja preselecciona el cliente
ASUNTO = "Solicitud de recojo - 6 pedidos"


def contar_operativos(db) -> dict:
    """Cuenta las filas de cada tabla operativa. Recibe la sesion."""
    return {t: db.execute(text(f'SELECT count(*) FROM "{t}"')).scalar() for t in TABLAS_OPERATIVAS}


def sembrar_correo_demo(db) -> int:
    """Reemplaza el correo de la demo por uno nuevo y pendiente, con el Excel adjunto. Recibe la sesion."""
    previas = db.query(Conversacion).filter(
        Conversacion.contraparte_email == EMAIL_CLIENTE, Conversacion.asunto == ASUNTO
    ).all()
    for conv in previas:
        mensajes = db.query(MensajeCorreo).filter(MensajeCorreo.conversacion_id == conv.id).all()
        for msg in mensajes:
            db.query(MensajeAdjunto).filter(MensajeAdjunto.mensaje_id == msg.id).delete()
            db.delete(msg)
        db.delete(conv)
    db.flush()

    with open(EXCEL, "rb") as f:
        contenido = f.read()
    ahora = datetime.utcnow()
    conv = Conversacion(
        contraparte_email=EMAIL_CLIENTE,
        contraparte_nombre=NOMBRE_CLIENTE,
        asunto=ASUNTO,
        asunto_normalizado=ASUNTO.strip().lower(),
        estado="PENDIENTE",
        no_leidos=1,
        ultimo_mensaje_en=ahora,
    )
    db.add(conv)
    db.flush()
    msg = MensajeCorreo(
        conversacion_id=conv.id,
        direccion="ENTRANTE",
        remitente=EMAIL_CLIENTE,
        destinatario="recojos@savasac.com",
        asunto=ASUNTO,
        cuerpo=(
            "Buenos días,\n\n"
            "Adjuntamos la solicitud de recojo de 6 pedidos de venta online para reparto en "
            "San Borja y Barranco. Los paquetes están listos en nuestro centro de distribución.\n\n"
            "Saludos,\nDespachos - " + NOMBRE_CLIENTE
        ),
        fecha=ahora,
        leido=False,
    )
    db.add(msg)
    db.flush()
    db.add(MensajeAdjunto(
        mensaje_id=msg.id,
        nombre_archivo="solicitud_recojo_falabella.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        tamano=len(contenido),
        contenido=contenido,
    ))
    return conv.id


def main():
    """Muestra lo que se borraria y, con --si, reinicia la demo. No recibe parametros."""
    db = SessionLocal()
    try:
        conteos = contar_operativos(db)
        print("Datos operativos actuales:", {t: n for t, n in conteos.items() if n})
        if "--si" not in sys.argv:
            print("Simulacion: no se borro nada. Agrega --si para reiniciar la demo.")
            return
        db.execute(text("TRUNCATE TABLE " + ", ".join(TABLAS_OPERATIVAS) + " RESTART IDENTITY CASCADE"))
        conv_id = sembrar_correo_demo(db)
        db.commit()
        print(f"OK: demo reiniciada. Correo de {NOMBRE_CLIENTE} pendiente en la Bandeja (conversacion {conv_id}).")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
