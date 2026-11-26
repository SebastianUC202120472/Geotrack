import io
from typing import Dict, List
from PIL import Image, ImageDraw
from sqlalchemy.orm import Session

from app.core import almacenamiento
from app.db import solo_lectura_core
from app.models.cola import ColaTrabajo
from app.services.motor_auditoria import procesar_auditoria_completa


def _escena_entrega_con_paquete() -> bytes:
    """Dibuja una fachada con puerta y una caja de envío en el piso (alta nitidez)."""
    img = Image.new("RGB", (640, 480), color=(242, 240, 235))
    d = ImageDraw.Draw(img)
    # Pared con ladrillos/líneas para nitidez real
    for y in range(20, 380, 24):
        d.line([(0, y), (640, y)], fill=(215, 210, 202), width=1)
    # Piso / vereda
    d.rectangle([0, 380, 640, 480], fill=(180, 182, 185), outline=(120, 120, 120))
    # Marco y puerta de domicilio
    d.rectangle([180, 70, 380, 380], fill=(115, 72, 42), outline=(60, 35, 18), width=4)
    d.rectangle([200, 95, 360, 220], outline=(80, 48, 25), width=3)
    d.rectangle([200, 240, 360, 360], outline=(80, 48, 25), width=3)
    d.ellipse([340, 225, 352, 237], fill=(220, 190, 80), outline="black")
    # Número de casa
    d.rectangle([400, 110, 465, 145], fill="white", outline="black", width=2)
    d.text((415, 122), "N° 245", fill="black")
    # Caja / paquete de cartón en primer plano
    d.rectangle([250, 290, 430, 420], fill=(198, 156, 109), outline=(90, 65, 35), width=3)
    d.line([(250, 340), (430, 340)], fill=(160, 120, 75), width=4)
    d.rectangle([290, 355, 390, 395], fill="white", outline="black", width=1)
    d.text((300, 368), "SAVA POD", fill="black")

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92)
    return buf.getvalue()


def _escena_solo_fachada_sin_paquete() -> bytes:
    """Dibuja únicamente una fachada/pared exterior sin paquete visible."""
    img = Image.new("RGB", (640, 480), color=(230, 236, 245))
    d = ImageDraw.Draw(img)
    for x in range(0, 640, 32):
        d.line([(x, 80), (x, 400)], fill=(150, 160, 175), width=2)
    for y in range(80, 400, 32):
        d.line([(0, y), (640, y)], fill=(150, 160, 175), width=2)
    d.rectangle([0, 400, 640, 480], fill=(160, 160, 160))
    d.rectangle([240, 140, 400, 400], fill=(90, 105, 125), outline="black", width=3)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def _escena_oscura_lente_tapado() -> bytes:
    """Imagen subexpuesta / negra (simula foto tomada con el bolsillo o de noche sin flash)."""
    img = Image.new("RGB", (500, 500), color=(8, 8, 10))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def sembrar_evidencias_demo(db: Session) -> Dict[str, int]:
    """Hidrata 4 escenarios de demostración sobre entregas existentes (o IDs demo)
    para inspeccionar el flujo completo en el panel sin alterar tablas del núcleo.
    """
    recientes = solo_lectura_core.obtener_evidencias_recientes(db, limite=10)

    img_valida = _escena_entrega_con_paquete()
    img_sin_paquete = _escena_solo_fachada_sin_paquete()
    img_oscura = _escena_oscura_lente_tapado()
    # Escenario 4: misma foto del escenario 1 re-comprimida (foto reciclada en otro pedido)
    with Image.open(io.BytesIO(img_valida)) as base_img:
        reciclada_img = base_img.resize((520, 390), Image.Resampling.LANCZOS)
        buf_dup = io.BytesIO()
        reciclada_img.save(buf_dup, format="JPEG", quality=78)
        img_reciclada = buf_dup.getvalue()

    escenarios = [
        {"bytes": img_valida, "gps_extra": None},
        {"bytes": img_sin_paquete, "gps_extra": "-12.0950,-77.0650"},
        {"bytes": img_oscura, "gps_extra": None},
        {"bytes": img_reciclada, "gps_extra": None},
    ]

    creadas = 0
    for idx, esc in enumerate(escenarios):
        if idx < len(recientes):
            ev = recientes[idx]
            ev_id = ev["evidencia_id"]
            ped_id = ev["pedido_id"]
            url_foto = ev["url_foto"]
            fecha = ev.get("fecha_entrega")
            p_lat = ev.get("pedido_latitud") if ev.get("pedido_latitud") is not None else -12.0464
            p_lon = ev.get("pedido_longitud") if ev.get("pedido_longitud") is not None else -77.0306
            gps_app = esc["gps_extra"] or ev.get("latitud_longitud_captura") or f"{p_lat:.4f},{p_lon:.4f}"
        else:
            ev_id = 9000 + idx
            ped_id = 9000 + idx
            url_foto = f"/media/evidencias/demo_pod_{idx + 1}.jpg"
            fecha = None
            p_lat, p_lon = -12.0464, -77.0306
            gps_app = esc["gps_extra"] or "-12.0465,-77.0305"

        almacenamiento.guardar_demo_memoria(url_foto, esc["bytes"])
        procesar_auditoria_completa(
            db=db,
            evidencia_id=ev_id,
            pedido_id=ped_id,
            url_foto=url_foto,
            datos_imagen=esc["bytes"],
            fecha_entrega_declarada=fecha,
            pedido_latitud=p_lat,
            pedido_longitud=p_lon,
            captura_gps_app=gps_app,
        )

        tarea = db.query(ColaTrabajo).filter(ColaTrabajo.evidencia_id == ev_id).first()
        if tarea:
            tarea.estado = "COMPLETADO"
            tarea.ultimo_error = None
            db.commit()

        creadas += 1

    return {"evidencias_demo_analizadas": creadas}
