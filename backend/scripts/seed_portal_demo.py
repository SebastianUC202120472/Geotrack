# Siembra la demostracion del portal de clientes: 5 empresas con acceso al portal y
# 250 pedidos del dia repartidos entre ellas, con sus rutas, historial y fotos POD.
#
# Borra SOLO los datos operativos. Conserva usuarios, vehiculos, parametros del sistema
# y la Bandeja de correos: los conductores y sus contrasenas siguen siendo los mismos.
#
# Correr dentro del contenedor backend:
#   docker exec geotrack-backend-1 python scripts/seed_portal_demo.py
import os
import random
import secrets
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text  # noqa: E402

from app.core import fechas  # noqa: E402
from app.core.codigos import (  # noqa: E402
    PREFIJO_CLIENTE, PREFIJO_DETALLE, PREFIJO_HISTORIAL, PREFIJO_PEDIDO, PREFIJO_RUTA,
    generar_codigo,
)
from app.core.security import get_password_hash  # noqa: E402
from app.db.database import SessionLocal  # noqa: E402
from app.models.cliente import ClienteCorporativo  # noqa: E402
from app.models.evidencia import EvidenciaEntrega  # noqa: E402
from app.models.historial import HistorialPedido  # noqa: E402
from app.models.pedido import Pedido  # noqa: E402
from app.models.ruta import Ruta, RutaDetalle  # noqa: E402
from app.models.usuario import Usuario  # noqa: E402
from app.models.vehiculo import Vehiculo  # noqa: E402

import datos_demo_portal as cat  # noqa: E402

# Conductores de la demostracion, en orden. El primero queda LIBRE a proposito: el
# backend rechaza asignar una ruta a un conductor que ya tiene una activa, y sin uno
# libre no se podria demostrar en vivo el despacho desde el panel.
CORREOS_CONDUCTORES = (
    "juan@prueba.com",
    "rosa.medina@sava.pe",
    "luis.chavez@sava.pe",
    "marta.silva@sava.pe",
)

# Tablas operativas que se vacian. NO incluye usuarios, conductor_perfiles, vehiculos,
# parametros_sistema ni correo_*.
TABLAS_A_VACIAR = (
    "ruta_detalles", "evidencias_entrega", "evidencias_recojo", "historial_pedidos",
    "incidencias", "reportes", "liquidaciones", "ubicaciones_conductor",
    "notificaciones", "verificaciones_portal", "solicitudes_restablecimiento",
    "pedidos", "rutas", "solicitudes_recojo", "clientes_corporativos",
)

DIR_SALIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "salida")
DIR_POD = os.path.join("uploads", "evidencias")


def vaciar_operativo(db):
    """Vacia las tablas de datos operativos reiniciando los IDs. Recibe la sesion.
    Se hace en una sola sentencia con CASCADE para no pelear con el orden de las FK."""
    db.execute(text("TRUNCATE TABLE " + ", ".join(TABLAS_A_VACIAR) + " RESTART IDENTITY CASCADE"))
    db.commit()


def conductores_de_la_demo(db) -> list:
    """Busca los 4 conductores de la demostracion con su vehiculo. Recibe la sesion.
    Aborta con un mensaje claro si falta alguno, en vez de sembrar a medias."""
    salida = []
    for correo in CORREOS_CONDUCTORES:
        u = db.query(Usuario).filter(Usuario.correo == correo).first()
        if not u:
            raise SystemExit(f"ERROR: falta el conductor {correo}. Crealo en el panel antes de sembrar.")
        v = db.query(Vehiculo).filter(
            Vehiculo.conductor_id == u.id, Vehiculo.eliminado_en.is_(None)).first()
        if not v:
            raise SystemExit(f"ERROR: el conductor {correo} no tiene vehiculo asignado.")
        salida.append({"usuario": u, "placa": v.placa})
    return salida


def crear_empresas(db) -> list:
    """Crea las 5 empresas cliente con su acceso al portal activo. Recibe la sesion.
    Devuelve la lista de ClienteCorporativo en el mismo orden del catalogo."""
    creados = []
    for datos in cat.EMPRESAS:
        c = ClienteCorporativo(
            razon_social=datos["razon_social"],
            identificador_unico=datos["ruc"],
            contacto=datos["correo_portal"],
            direccion_origen=datos["direccion_origen"],
            distrito=datos["direccion_origen"].split(",")[1].strip(),
            codigo_acceso=datos["codigo_acceso"],
            clave_hash=get_password_hash(datos["clave"]),
            correo_portal=datos["correo_portal"],
            acceso_activo=True,
        )
        db.add(c)
        creados.append(c)
    db.flush()
    for c in creados:
        c.codigo = generar_codigo(PREFIJO_CLIENTE, c.id)
    return creados


def _momento(base: datetime, hora: int, minuto: int) -> datetime:
    """Devuelve una marca UTC naive para una hora local del dia sembrado.
    Recibe el inicio UTC del dia local y la hora/minuto locales."""
    return base + timedelta(hours=hora, minutes=minuto)


def momentos_de_cierre(pedidos) -> dict:
    """Calcula el instante en que se cerro cada pedido terminal. Recibe [[pedido, estado,
    indice], ...] y devuelve {pedido_id: momento UTC}.
    Se calcula UNA sola vez y lo comparten el historial, la fecha de entrega, la
    evidencia y el detalle de ruta: si cada uno inventara su hora, la linea de tiempo
    del portal contradiria la hora que muestra el panel corporativo.
    Las 11:00-17:59 locales van siempre despues del ultimo paso intermedio (10:xx)."""
    inicio_dia, _ = fechas.rango_utc_del_dia()
    return {
        p.id: _momento(inicio_dia, 11 + indice % 7, indice % 60)
        for p, estado, indice in pedidos
        if estado in ("ENTREGADO", "FALLIDO")
    }


def crear_pedidos(db, empresas) -> list:
    """Crea los 250 pedidos del dia con su estado, destinatario y coordenadas.
    Recibe la sesion y la lista de empresas. Devuelve [[pedido, estado, indice], ...]."""
    inicio_dia, _ = fechas.rango_utc_del_dia()
    azar = random.Random(20260918)   # semilla fija: la siembra es reproducible
    distritos = list(cat.DISTRITOS)
    pedidos = []
    indice = 0
    for pos_empresa, (empresa, datos) in enumerate(zip(empresas, cat.EMPRESAS)):
        for i, estado in enumerate(cat.reparto_estados(50)):
            # Los pendientes se concentran en pocas zonas; el resto se reparte por toda Lima.
            if estado == "LISTO_PARA_ENVIO":
                distrito = cat.DISTRITOS_PENDIENTES[i % len(cat.DISTRITOS_PENDIENTES)]
            else:
                distrito = distritos[(indice + pos_empresa) % len(distritos)]
            lat, lng = cat.DISTRITOS[distrito]
            persona = cat.destinatario(indice)
            p = Pedido(
                referencia_externa=f"{datos['prefijo_ref']}-{1000 + i}",
                cliente_id=empresa.id,
                cliente_origen=empresa.razon_social,
                direccion_destino=cat.direccion(indice, distrito),
                nombre_destinatario=persona["nombre"],
                telefono_destinatario=persona["telefono"],
                dni_destinatario=persona["dni"],
                distrito=distrito,
                latitud=round(lat + azar.uniform(-0.012, 0.012), 6),
                longitud=round(lng + azar.uniform(-0.012, 0.012), 6),
                peso_kg=round(azar.uniform(0.5, 12.0), 1),
                volumen_m3=round(azar.uniform(0.01, 0.35), 3),
                estado=estado,
                fecha_creacion=_momento(inicio_dia, 7, 10 + indice % 45),
            )
            db.add(p)
            pedidos.append([p, estado, indice])
            indice += 1
    db.flush()
    for p, _, _ in pedidos:
        p.codigo = generar_codigo(PREFIJO_PEDIDO, p.id)
    return pedidos


# Cadena de estados por la que pasa cada pedido antes de llegar a su estado final.
_CAMINO = {
    "ENTREGADO": ["POR_RECOGER", "LISTO_PARA_ENVIO", "ASIGNADO", "EN_RUTA", "ENTREGADO"],
    "FALLIDO": ["POR_RECOGER", "LISTO_PARA_ENVIO", "ASIGNADO", "EN_RUTA", "FALLIDO"],
    "EN_RUTA": ["POR_RECOGER", "LISTO_PARA_ENVIO", "ASIGNADO", "EN_RUTA"],
    "LISTO_PARA_ENVIO": ["POR_RECOGER", "LISTO_PARA_ENVIO"],
    "OBSERVADO": ["POR_RECOGER", "OBSERVADO"],
}


def crear_historial(db, pedidos, admin_id, cierres):
    """Inserta la trazabilidad completa de cada pedido. Recibe la sesion, los pedidos,
    el id del admin y los momentos de cierre.
    Los pasos intermedios van de 07:00 a 10:xx (una hora cada uno, asi la linea de
    tiempo sale en orden) y el paso final reutiliza el momento de cierre compartido."""
    inicio_dia, _ = fechas.rango_utc_del_dia()
    filas = []
    for p, estado, indice in pedidos:
        anterior = None
        camino = _CAMINO[estado]
        for paso, nuevo in enumerate(camino):
            es_cierre = paso == len(camino) - 1 and p.id in cierres
            filas.append(HistorialPedido(
                pedido_id=p.id,
                estado_anterior=anterior,
                estado_nuevo=nuevo,
                usuario_id=admin_id,
                fecha_utc=(cierres[p.id] if es_cierre
                           else _momento(inicio_dia, 7 + paso, (indice + paso * 11) % 60)),
            ))
            anterior = nuevo
    db.add_all(filas)
    db.flush()
    for h in filas:
        h.codigo = generar_codigo(PREFIJO_HISTORIAL, h.id)


def _agrupar(pedidos, estados) -> dict:
    """Agrupa pedidos por distrito. Recibe la lista [[pedido, estado, indice], ...] y los
    estados que interesan. Devuelve {distrito: [pedido, ...]}."""
    grupos = {}
    for p, estado, _ in pedidos:
        if estado in estados:
            grupos.setdefault(p.distrito, []).append(p)
    return grupos


def crear_rutas(db, pedidos, conductores, cierres) -> dict:
    """Crea las rutas finalizadas y las que estan en curso, con sus paradas.
    Recibe la sesion, los pedidos, los conductores y los momentos de cierre.
    Devuelve {pedido_id: detalle}.
    Los conductores 2, 3 y 4 cargan las rutas; el primero queda libre para la demo."""
    inicio_dia, _ = fechas.rango_utc_del_dia()
    con_ruta = conductores[1:]
    detalles_por_pedido = {}
    rutas = []

    # Una ruta FINALIZADA por distrito con los pedidos ya cerrados (entregados y fallidos).
    for turno, (distrito, grupo) in enumerate(sorted(_agrupar(pedidos, {"ENTREGADO", "FALLIDO"}).items())):
        c = con_ruta[turno % len(con_ruta)]
        rutas.append({
            "nombre": f"Ruta {distrito}", "estado": "FINALIZADA", "conductor": c,
            "pedidos": grupo, "salida": _momento(inicio_dia, 10, 0), "fin": _momento(inicio_dia, 18, 30),
        })

    # Una ruta EN_PROGRESO por conductor con los pedidos que van en camino.
    en_camino = [p for p, estado, _ in pedidos if estado == "EN_RUTA"]
    tamano = (len(en_camino) + len(con_ruta) - 1) // len(con_ruta)
    for turno, c in enumerate(con_ruta):
        grupo = en_camino[turno * tamano:(turno + 1) * tamano]
        if not grupo:
            continue
        rutas.append({
            "nombre": f"Ruta tarde {grupo[0].distrito}", "estado": "EN_PROGRESO", "conductor": c,
            "pedidos": grupo, "salida": _momento(inicio_dia, 14, 0), "fin": None,
        })

    for datos in rutas:
        r = Ruta(
            nombre=datos["nombre"], tipo="ENTREGA", estado=datos["estado"],
            fecha_creacion=_momento(inicio_dia, 8, 30),
            fecha_salida=datos["salida"], fecha_fin=datos["fin"],
            km_estimado=round(4.5 + len(datos["pedidos"]) * 1.4, 1),
            km_ahorrado=round(len(datos["pedidos"]) * 0.45, 1),
            vehiculo_placa=datos["conductor"]["placa"],
            conductor_id=datos["conductor"]["usuario"].id,
        )
        db.add(r)
        db.flush()
        r.codigo = generar_codigo(PREFIJO_RUTA, r.id)
        nuevos = []
        for orden, p in enumerate(datos["pedidos"], start=1):
            if p.estado == "ENTREGADO":
                estado_entrega, motivo = "ENTREGADO", None
            elif p.estado == "FALLIDO":
                estado_entrega, motivo = "FALLIDO", "Destinatario ausente en la direccion"
            else:
                estado_entrega, motivo = "PENDIENTE", None
            d = RutaDetalle(
                ruta_id=r.id, pedido_id=p.id, secuencia=orden,
                estado_entrega=estado_entrega, motivo_fallo=motivo,
                fecha_gestion=cierres.get(p.id) if estado_entrega != "PENDIENTE" else None,
            )
            db.add(d)
            nuevos.append(d)
            detalles_por_pedido[p.id] = d
        db.flush()
        for d in nuevos:
            d.codigo = generar_codigo(PREFIJO_DETALLE, d.id)
    return detalles_por_pedido


def _imagen_pod(codigo: str, nombre: str, cuando: str):
    """Dibuja una constancia de entrega. Recibe el codigo del pedido, el nombre de quien
    recibio y la hora. Devuelve la imagen de Pillow lista para guardar."""
    from PIL import Image, ImageDraw, ImageFont
    try:
        fuente_titulo = ImageFont.load_default(size=26)
        fuente = ImageFont.load_default(size=17)
    except TypeError:   # Pillow antiguo: load_default no acepta tamano
        fuente_titulo = fuente = ImageFont.load_default()
    img = Image.new("RGB", (520, 380), (233, 239, 245))
    d = ImageDraw.Draw(img)
    d.rectangle([14, 14, 506, 366], outline=(15, 43, 74), width=3)
    d.rectangle([44, 96, 196, 240], fill=(198, 166, 122), outline=(126, 98, 62), width=3)
    d.line([44, 168, 196, 168], fill=(126, 98, 62), width=3)
    d.line([120, 96, 120, 240], fill=(126, 98, 62), width=3)
    d.text((44, 44), "PRUEBA DE ENTREGA", font=fuente_titulo, fill=(15, 43, 74))
    d.text((226, 108), f"Pedido: {codigo}", font=fuente, fill=(20, 45, 72))
    d.text((226, 142), f"Recibido por: {nombre}", font=fuente, fill=(20, 45, 72))
    d.text((226, 176), f"Hora: {cuando}", font=fuente, fill=(20, 45, 72))
    d.text((226, 210), "Estado: CONFORME", font=fuente, fill=(24, 122, 70))
    d.text((44, 292), "SAVA S.A.C. - GeoTrack", font=fuente, fill=(90, 110, 132))
    d.text((44, 320), "Imagen de demostracion", font=fuente, fill=(150, 165, 182))
    return img


def crear_evidencias(db, pedidos, detalles, cierres):
    """Genera la foto POD de cada pedido entregado y la registra. Recibe la sesion, los
    pedidos, los detalles de ruta y los momentos de cierre. Escribe en uploads/evidencias
    con nombre no enumerable (sufijo aleatorio), igual que las fotos que sube la app movil."""
    os.makedirs(DIR_POD, exist_ok=True)
    for p, estado, indice in pedidos:
        if estado != "ENTREGADO":
            continue
        momento = cierres[p.id]
        # La hora impresa en la constancia es la LOCAL de la operacion; en la BD la
        # marca se guarda en UTC naive, como el resto del sistema.
        etiqueta_hora = momento.replace(tzinfo=timezone.utc).astimezone(fechas.zona()).strftime("%H:%M")
        archivo = f"pod_{p.codigo}_{secrets.token_hex(4)}.jpg"
        _imagen_pod(p.codigo, p.nombre_destinatario, etiqueta_hora).save(
            os.path.join(DIR_POD, archivo), "JPEG", quality=70)
        url = f"/media/evidencias/{archivo}"
        db.add(EvidenciaEntrega(
            pedido_id=p.id, url_foto=url,
            latitud_longitud_captura=f"{p.latitud},{p.longitud}", fecha_hora=momento))
        p.fecha_entrega = momento
        if p.id in detalles:
            detalles[p.id].url_evidencia = url


def escribir_hoja(pedidos):
    """Escribe la hoja de credenciales y de pedidos de ejemplo. Recibe los pedidos.
    Devuelve la ruta del archivo generado."""
    os.makedirs(DIR_SALIDA, exist_ok=True)
    ruta = os.path.join(DIR_SALIDA, "credenciales_portal_demo.md")
    etiqueta = {"ENTREGADO": "Entregado", "EN_RUTA": "En camino", "LISTO_PARA_ENVIO": "Por salir",
                "FALLIDO": "Reprogramado", "OBSERVADO": "En gestion"}
    lineas = [
        "# Portal de clientes — hoja de sustentacion",
        "",
        f"Generada el {datetime.now().strftime('%d/%m/%Y %H:%M')}. Portal: http://localhost:8080/portal",
        "",
        "## Acceso de empresa",
        "",
        "| Empresa | Codigo de acceso | Clave | Correo del OTP |",
        "|---|---|---|---|",
    ]
    for e in cat.EMPRESAS:
        lineas.append(f"| {e['razon_social']} | `{e['codigo_acceso']}` | `{e['clave']}` | {e['correo_portal']} |")
    lineas += [
        "",
        "El codigo de verificacion aparece en la propia pantalla (modo demostracion, SMTP apagado).",
        "",
        "## Rastreo de persona natural",
        "",
        "Se puede buscar con el codigo interno de SAVA o con la referencia del retail.",
        "El portal pide los **ultimos 4 digitos** del DNI, no el DNI completo.",
        "",
        "| Empresa | Codigo SAVA | Referencia retail | Estado | Ultimos 4 del DNI |",
        "|---|---|---|---|---|",
    ]
    # Un ejemplo por empresa y por estado, para tener a mano uno de cada caso.
    vistos = set()
    for p, estado, _ in pedidos:
        clave = (p.cliente_origen, estado)
        if clave in vistos:
            continue
        vistos.add(clave)
        lineas.append(
            f"| {p.cliente_origen} | `{p.codigo}` | `{p.referencia_externa}` | "
            f"{etiqueta[estado]} | `{p.dni_destinatario[-4:]}` |")
    lineas += ["", "## Conductores", ""]
    for correo in CORREOS_CONDUCTORES:
        nota = " — SIN ruta activa, listo para el despacho en vivo" if correo == CORREOS_CONDUCTORES[0] else ""
        lineas.append(f"- `{correo}`{nota}")
    lineas.append("")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas))
    return ruta


def main():
    """Ejecuta la siembra completa de la demostracion del portal. Sin input."""
    db = SessionLocal()
    # Tras cada commit los objetos siguen usables sin volver a consultarlos: la hoja de
    # credenciales y la generacion de POD leen los 250 pedidos ya cargados, y con el
    # comportamiento normal cada lectura seria un viaje mas a Supabase.
    db.expire_on_commit = False
    try:
        conductores = conductores_de_la_demo(db)
        admin = db.query(Usuario).filter(Usuario.rol == "admin").order_by(Usuario.id).first()
        admin_id = admin.id if admin else None

        print("Vaciando datos operativos...")
        vaciar_operativo(db)

        print("Creando empresas...")
        empresas = crear_empresas(db)

        print("Creando pedidos...")
        pedidos = crear_pedidos(db, empresas)

        cierres = momentos_de_cierre(pedidos)

        print("Creando historial...")
        crear_historial(db, pedidos, admin_id, cierres)

        print("Creando rutas...")
        detalles = crear_rutas(db, pedidos, conductores, cierres)
        # Se cierra la transaccion ANTES de dibujar las imagenes. Generar 150 JPEG dentro
        # de ella la mantendria abierta un par de minutos sobre tablas recien truncadas, y
        # cualquier reinicio del backend en ese rato se quedaria esperando el lock hasta
        # agotar el statement_timeout de Supabase.
        db.commit()

        print("Generando fotos POD...")
        crear_evidencias(db, pedidos, detalles, cierres)
        db.commit()
        ruta = escribir_hoja(pedidos)
        print(f"\nOK: {len(empresas)} empresas y {len(pedidos)} pedidos sembrados.")
        print(f"Hoja de credenciales: {ruta}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
