# Siembra un correo de "solicitud de recojo" en la Bandeja (pestaña "Solicitud del cliente")
# con el Excel de 200 pedidos adjunto, como punto de partida del flujo de prueba.
# Correr dentro del contenedor backend:  python scripts/seed_solicitud_correo.py
import os
import sys
from datetime import datetime

# Asegura que /app (raíz del backend) esté en el path para poder importar el paquete app.*
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal  # noqa: E402
from app.models.correo import Conversacion, MensajeCorreo, MensajeAdjunto  # noqa: E402

EXCEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "solicitud_recojo_200.xlsx")
# El cliente que SOLICITA el recojo (SAVA es el operador, no el cliente).
EMAIL_CLIENTE = "logistica@ripley.com.pe"
NOMBRE_CLIENTE = "Ripley S.A."
ASUNTO = "Solicitud de recojo - 200 pedidos"


def main():
    # Lee el Excel y crea la conversación entrante + su mensaje + el adjunto (en la BD).
    with open(EXCEL, "rb") as f:
        contenido = f.read()

    db = SessionLocal()
    try:
        conv = Conversacion(
            contraparte_email=EMAIL_CLIENTE,
            contraparte_nombre=NOMBRE_CLIENTE,
            asunto=ASUNTO,
            asunto_normalizado=ASUNTO.strip().lower(),
            estado="PENDIENTE",
            no_leidos=1,
            ultimo_mensaje_en=datetime.utcnow(),
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
                "Adjunto la solicitud de recojo de nuestros 200 pedidos para que coordinen "
                "el recojo en nuestro almacén.\n\nSaludos,\n" + NOMBRE_CLIENTE
            ),
            fecha=datetime.utcnow(),
            leido=False,
        )
        db.add(msg)
        db.flush()

        db.add(MensajeAdjunto(
            mensaje_id=msg.id,
            nombre_archivo="solicitud_recojo_200.xlsx",
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            tamano=len(contenido),
            contenido=contenido,
        ))
        db.commit()
        print(f"OK: correo de solicitud sembrado (conversacion id={conv.id}, adjunto {len(contenido)} bytes).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
