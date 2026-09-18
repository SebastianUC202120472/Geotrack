# Siembra UNA solicitud de recojo de ZARA en la Bandeja, con un Excel de 50 pedidos
# adjunto, para recorrer el flujo completo a mano: aceptar la solicitud -> armar la ruta
# de recojo -> recoger con la app -> ingreso en almacen -> despachar por zonas -> entregar.
#
# A diferencia de seed_portal_demo.py, este script NO borra nada ni crea pedidos: deja
# el correo en la Bandeja tal como llegaria de un cliente real. Los pedidos los crea el
# admin al aceptar la solicitud desde el panel.
#
# Correr dentro del contenedor backend:
#   docker exec geotrack-backend-1 python scripts/seed_solicitud_zara.py
import io
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openpyxl import Workbook  # noqa: E402

from app.core.codigos import PREFIJO_CLIENTE, generar_codigo  # noqa: E402
from app.core.security import get_password_hash  # noqa: E402
from app.db.database import SessionLocal  # noqa: E402
from app.models.cliente import ClienteCorporativo  # noqa: E402
from app.models.correo import Conversacion, MensajeAdjunto, MensajeCorreo  # noqa: E402
from app.models.parametro import ParametroSistema  # noqa: E402
from app.services.geocoder import obtener_coordenadas  # noqa: E402

EMPRESA = {
    "razon_social": "Zara Peru S.A.",
    "ruc": "20512395811",
    # Centro de distribucion, distinto al de las otras cinco empresas sembradas.
    "direccion_origen": "Av. Los Rosales 250, Santa Anita, Lima, Peru",
    "codigo_acceso": "ZARA",
    "clave": "Zara2026",
    "correo_portal": "logistica@zara.com.pe",
    "contacto": "Mariana Robles - Jefa de Distribucion",
}

ASUNTO = "Solicitud de recojo - 50 pedidos temporada"
ARCHIVO = "solicitud_recojo_zara_50.xlsx"

# Zonas de reparto de ZARA: el cono norte, el este y el sur. Ninguna coincide con las de
# seed_portal_demo.py, para que la Agrupacion por Zonas muestre zonas nuevas y no se
# mezclen con los pedidos que ya estan en el sistema.
VIAS_POR_DISTRITO = {
    "Los Olivos": ("Av. Alfredo Mendiola", "Av. Carlos Izaguirre", "Av. Antunez de Mayolo"),
    "San Martin de Porres": ("Av. Peru", "Av. Tomas Valle"),
    "Independencia": ("Av. Tupac Amaru", "Av. Gerardo Unger"),
    "Comas": ("Av. Universitaria", "Av. Tupac Amaru"),
    "Ate": ("Av. Nicolas Ayllon", "Av. Metropolitana"),
    "Santa Anita": ("Av. Los Ruisenores", "Av. Francisco Bolognesi"),
    "Chorrillos": ("Av. Huaylas", "Av. Defensores del Morro"),
    "San Juan de Miraflores": ("Av. Los Heroes", "Av. Pedro Miotta"),
    "Callao": ("Av. Elmer Faucett", "Av. Saenz Pena"),
    "Brena": ("Av. Venezuela", "Av. Arica"),
}

_NOMBRES = (
    "Valeria", "Sebastian", "Camila", "Mateo", "Fernanda", "Joaquin", "Renata", "Alonso",
    "Ximena", "Facundo", "Antonella", "Thiago", "Micaela", "Emiliano", "Alessandra",
    "Rodrigo", "Luciana", "Gabriel", "Isabella", "Santiago",
)
_APELLIDOS = (
    "Delgado", "Espinoza", "Carrion", "Montalvo", "Iparraguirre", "Valdivia", "Alarcon",
    "Meza", "Barrantes", "Cueva",
)


def filas_de_pedidos() -> list:
    """Genera las 50 filas del Excel de la solicitud. Sin input.
    Reparte los pedidos por las diez zonas de VIAS_POR_DISTRITO y usa un rango de DNI
    distinto al de la otra siembra, para que no se crucen los datos de prueba."""
    distritos = list(VIAS_POR_DISTRITO)
    filas = []
    for i in range(50):
        distrito = distritos[i % len(distritos)]
        vias = VIAS_POR_DISTRITO[distrito]
        via = vias[(i // len(distritos)) % len(vias)]
        numero = 200 + (i * 47) % 2400
        nombre = f"{_NOMBRES[i % len(_NOMBRES)]} {_APELLIDOS[(i // len(_NOMBRES)) % len(_APELLIDOS)]}"
        filas.append({
            "numero_tracking": f"ZR-{2001 + i}",
            "razon_social_cliente": EMPRESA["razon_social"],
            "direccion_destino": f"{via} {numero}, {distrito}, Lima, Peru",
            "nombre_destinatario": nombre,
            "telefono_destinatario": f"9{20000000 + i * 131:08d}"[:9],
            "dni_destinatario": f"{72000000 + i * 13:08d}",
            "peso_kg": round(0.4 + (i % 9) * 0.7, 1),
            "volumen_m3": round(0.01 + (i % 7) * 0.012, 3),
        })
    return filas


def construir_excel(filas) -> bytes:
    """Arma el .xlsx de la solicitud en memoria. Recibe las filas normalizadas.
    Las columnas son las que espera pedido_service.parsear_filas_excel."""
    columnas = ["numero_tracking", "razon_social_cliente", "direccion_destino",
                "nombre_destinatario", "telefono_destinatario", "dni_destinatario",
                "peso_kg", "volumen_m3"]
    wb = Workbook()
    ws = wb.active
    ws.title = "Pedidos"
    ws.append(columnas)
    for fila in filas:
        ws.append([fila[c] for c in columnas])
    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def asegurar_cliente(db) -> ClienteCorporativo:
    """Crea o actualiza la empresa ZARA con su punto de recojo geocodificado. Recibe la
    sesion. Sin coordenadas el panel rechaza aceptar la solicitud, asi que se geocodifica
    aqui y se aborta si el proveedor no resuelve la direccion."""
    cliente = (
        db.query(ClienteCorporativo)
        .filter(ClienteCorporativo.identificador_unico == EMPRESA["ruc"])
        .first()
    )
    if cliente is None:
        cliente = ClienteCorporativo(identificador_unico=EMPRESA["ruc"])
        db.add(cliente)

    lat, lng = obtener_coordenadas(EMPRESA["direccion_origen"])
    if lat is None or lng is None:
        raise SystemExit("ERROR: no se pudo geocodificar el punto de recojo de ZARA.")

    cliente.razon_social = EMPRESA["razon_social"]
    cliente.contacto = EMPRESA["contacto"]
    cliente.direccion_origen = EMPRESA["direccion_origen"]
    cliente.distrito = EMPRESA["direccion_origen"].split(",")[1].strip()
    cliente.latitud = lat
    cliente.longitud = lng
    cliente.eliminado_en = None
    cliente.codigo_acceso = EMPRESA["codigo_acceso"]
    cliente.clave_hash = get_password_hash(EMPRESA["clave"])
    cliente.correo_portal = EMPRESA["correo_portal"]
    cliente.acceso_activo = True
    db.flush()
    if not cliente.codigo:
        cliente.codigo = generar_codigo(PREFIJO_CLIENTE, cliente.id)
    return cliente


def sembrar_correo(db, contenido: bytes) -> int:
    """Deja la solicitud como un correo entrante sin leer en la Bandeja. Recibe la sesion
    y los bytes del Excel. Devuelve el id de la conversacion.
    Si ya existe una conversacion con el mismo asunto, la reutiliza en vez de duplicarla."""
    existente = (
        db.query(Conversacion)
        .filter(Conversacion.contraparte_email == EMPRESA["correo_portal"],
                Conversacion.asunto_normalizado == ASUNTO.strip().lower())
        .first()
    )
    if existente:
        print(f"Aviso: ya existia la conversacion id={existente.id}; se reutiliza.")
        existente.estado = "PENDIENTE"
        existente.no_leidos = 1
        existente.ultimo_mensaje_en = datetime.utcnow()
        db.flush()
        return existente.id

    conv = Conversacion(
        contraparte_email=EMPRESA["correo_portal"],
        contraparte_nombre=EMPRESA["razon_social"],
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
        remitente=EMPRESA["correo_portal"],
        destinatario="recojos@savasac.com",
        asunto=ASUNTO,
        cuerpo=(
            "Estimados,\n\n"
            "Adjunto la relacion de 50 pedidos de la nueva temporada para que coordinen el "
            "recojo en nuestro centro de distribucion de Santa Anita.\n\n"
            "El personal de despacho atiende de 9:00 a 18:00.\n\n"
            "Saludos cordiales,\n"
            f"{EMPRESA['contacto']}\n{EMPRESA['razon_social']}"
        ),
        fecha=datetime.utcnow(),
        leido=False,
    )
    db.add(msg)
    db.flush()

    db.add(MensajeAdjunto(
        mensaje_id=msg.id,
        nombre_archivo=ARCHIVO,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        tamano=len(contenido),
        contenido=contenido,
    ))
    return conv.id


def agregar_a_ayuda_demo(db):
    """Suma ZARA a las credenciales que el portal muestra en modo demostracion. Recibe la
    sesion. No pasa nada si la ayuda todavia no existe: la escribe seed_portal_demo.py."""
    fila = (
        db.query(ParametroSistema)
        .filter(ParametroSistema.categoria == "portal_demo", ParametroSistema.clave == "ayuda")
        .first()
    )
    if not fila or not fila.valor_json:
        return
    datos = dict(fila.valor_json)
    empresas = [e for e in datos.get("empresas", []) if e.get("codigo") != EMPRESA["codigo_acceso"]]
    empresas.append({
        "nombre": EMPRESA["razon_social"],
        "codigo": EMPRESA["codigo_acceso"],
        "clave": EMPRESA["clave"],
    })
    datos["empresas"] = empresas
    fila.valor_json = datos
    # Reasignar el dict no basta para que SQLAlchemy detecte el cambio en una columna JSON.
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(fila, "valor_json")


def main():
    """Siembra la empresa ZARA y su solicitud de recojo en la Bandeja. Sin input."""
    filas = filas_de_pedidos()
    contenido = construir_excel(filas)
    db = SessionLocal()
    try:
        cliente = asegurar_cliente(db)
        conv_id = sembrar_correo(db, contenido)
        agregar_a_ayuda_demo(db)
        db.commit()
        zonas = sorted({f["direccion_destino"].split(",")[1].strip() for f in filas})
        print(f"OK: empresa {cliente.razon_social} lista (codigo {cliente.codigo}).")
        print(f"    Punto de recojo: {cliente.direccion_origen} ({cliente.latitud}, {cliente.longitud})")
        print(f"    Correo sembrado en la Bandeja: conversacion id={conv_id}, adjunto {len(contenido)} bytes.")
        print(f"    {len(filas)} pedidos en {len(zonas)} zonas: {', '.join(zonas)}")
        print(f"    Acceso al portal: {EMPRESA['codigo_acceso']} / {EMPRESA['clave']}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
