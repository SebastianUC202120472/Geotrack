# Tablero por periodo (C34-01, C34-02) e indicadores del proyecto In.OE.1-4 del Charter (C34-03).
import io
from datetime import date, datetime, time, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core import fechas
from app.models.correo import MensajeCorreo
from app.models.evidencia import EvidenciaEntrega
from app.models.historial import HistorialPedido
from app.models.pedido import Pedido
from app.models.reclamo import Reclamo
from app.models.ruta import Ruta
from app.models.solicitud_recojo import SolicitudRecojo
from app.services import parametro_service

PERIODOS = ("dia", "semana", "mes")
# Estados que ya no esperan entrega: el resto cuenta como pendiente.
ESTADOS_CERRADOS = ("ENTREGADO", "CANCELADO")


def rango(periodo: str | None = None, desde: date | None = None, hasta: date | None = None) -> tuple[date, date]:
    """Dias locales (inclusive) del periodo: hoy, semana (lunes a hoy) o mes (dia 1 a hoy); o el
    rango explicito desde/hasta. Recibe el periodo o las fechas."""
    hoy = fechas.hoy_local()
    if desde or hasta:
        desde, hasta = desde or hasta, hasta or hoy
        if desde > hasta:
            raise HTTPException(status_code=400, detail="La fecha inicial no puede ser posterior a la final")
        if (hasta - desde).days > 366:
            raise HTTPException(status_code=400, detail="El rango no puede superar un año")
        return desde, hasta
    periodo = (periodo or "dia").lower()
    if periodo not in PERIODOS:
        raise HTTPException(status_code=400, detail="Periodo inválido: usa dia, semana o mes")
    if periodo == "semana":
        return hoy - timedelta(days=hoy.weekday()), hoy
    if periodo == "mes":
        return hoy.replace(day=1), hoy
    return hoy, hoy


def _utc(dia: date) -> datetime:
    """Inicio del dia local expresado en UTC naive (como se guarda en la BD). Recibe el dia."""
    return datetime.combine(dia, time.min, tzinfo=fechas.zona()).astimezone(timezone.utc).replace(tzinfo=None)


def _limites(desde: date, hasta: date) -> tuple[datetime, datetime]:
    """[inicio, fin) en UTC naive del rango de dias locales. Recibe desde y hasta."""
    return _utc(desde), _utc(hasta + timedelta(days=1))


def _eventos(db: Session, estados: tuple, ini: datetime, fin: datetime):
    """Eventos del historial con esos estados en el rango (pedido_id, estado, fecha). Recibe estados y limites."""
    return (
        db.query(HistorialPedido.pedido_id, HistorialPedido.estado_nuevo, HistorialPedido.fecha_utc)
        .filter(HistorialPedido.estado_nuevo.in_(estados), HistorialPedido.fecha_utc >= ini, HistorialPedido.fecha_utc < fin)
        .all()
    )


def _rutas_cerradas(db: Session, ini: datetime, fin: datetime):
    """Rutas de entrega finalizadas en el rango. Recibe los limites."""
    return (
        db.query(Ruta)
        .filter(Ruta.fecha_fin >= ini, Ruta.fecha_fin < fin, func.coalesce(Ruta.tipo, "ENTREGA") != "RECOJO")
        .all()
    )


def _soles_por_km(db: Session) -> float:
    """Costo de combustible por km segun los parametros (consumo L/100 km y S/ por litro)."""
    c = parametro_service.obtener_combustible(db)
    return c["consumo_l_100km"] / 100.0 * c["precio_soles_litro"]


def kpis(db: Session, periodo: str | None = None, desde: date | None = None, hasta: date | None = None) -> dict:
    """KPIs del tablero en el periodo: % de cumplimiento (entregados sobre gestionados), entregados,
    fallidos, pendientes de hoy, km y ahorro de la flota en S/, y la serie por dia. Recibe el periodo."""
    d, h = rango(periodo, desde, hasta)
    ini, fin = _limites(d, h)
    eventos = _eventos(db, ("ENTREGADO", "FALLIDO"), ini, fin)
    entregados = sum(1 for _, e, _ in eventos if e == "ENTREGADO")
    fallidos = sum(1 for _, e, _ in eventos if e == "FALLIDO")
    gestionados = entregados + fallidos
    pendientes = db.query(func.count(Pedido.id)).filter(Pedido.estado.notin_(ESTADOS_CERRADOS)).scalar() or 0

    rutas = _rutas_cerradas(db, ini, fin)
    km = sum(r.km_estimado or 0 for r in rutas)
    km_ahorrado = sum(r.km_ahorrado or 0 for r in rutas)
    bateria = consumo_bateria(rutas)

    serie = {}
    dia = d
    while dia <= h:
        serie[dia] = {"dia": dia.isoformat(), "entregados": 0, "fallidos": 0}
        dia += timedelta(days=1)
    for _, estado, momento in eventos:
        fila = serie.get(fechas.fecha_local_de(momento))
        if fila:
            fila["entregados" if estado == "ENTREGADO" else "fallidos"] += 1

    return {
        "desde": d.isoformat(), "hasta": h.isoformat(),
        "entregados": entregados, "fallidos": fallidos, "gestionados": gestionados,
        "cumplimiento": round(entregados / gestionados * 100, 1) if gestionados else None,
        "pendientes": pendientes,
        "rutas_cerradas": len(rutas),
        "km_recorridos": round(km, 1),
        "km_ahorrados": round(km_ahorrado, 1),
        "ahorro_soles": round(km_ahorrado * _soles_por_km(db), 2),
        "bateria": bateria,
        "serie": list(serie.values()),
    }


def consumo_bateria(rutas) -> dict:
    """Consumo de bateria del celular en las jornadas medidas (EX-15): puntos porcentuales gastados
    y por hora de jornada, en promedio. Solo cuentan rutas con al menos 30 min de lecturas. Recibe las rutas."""
    medidas = []
    for r in rutas:
        if r.bateria_inicio is None or r.bateria_fin is None or not (r.bateria_inicio_en and r.bateria_fin_en):
            continue
        horas = (r.bateria_fin_en - r.bateria_inicio_en).total_seconds() / 3600
        if horas >= 0.5:
            gasto = (r.bateria_inicio - r.bateria_fin) * 100
            medidas.append((gasto, horas))
    if not medidas:
        return {"jornadas": 0, "gasto_promedio": None, "por_hora": None, "horas_promedio": None}
    gasto = sum(g for g, _ in medidas) / len(medidas)
    horas = sum(h for _, h in medidas) / len(medidas)
    return {"jornadas": len(medidas), "gasto_promedio": round(gasto, 1),
            "por_hora": round(sum(g for g, _ in medidas) / sum(h for _, h in medidas), 1),
            "horas_promedio": round(horas, 1)}


def _registro_de_lotes(db: Session, ini: datetime, fin: datetime) -> dict:
    """In.OE.1: minutos desde que llega el correo de la solicitud hasta que el lote queda registrado.
    Solo cuentan los lotes que vinieron por correo (los manuales no tienen hora de llegada)."""
    lotes = db.query(SolicitudRecojo).filter(SolicitudRecojo.fecha_creacion >= ini, SolicitudRecojo.fecha_creacion < fin).all()
    minutos, pedidos = [], 0
    for lote in lotes:
        pedidos += db.query(func.count(Pedido.id)).filter(Pedido.recojo_id == lote.id).scalar() or 0
        if not lote.conversacion_id:
            continue
        llegada = (
            db.query(func.min(MensajeCorreo.fecha))
            .filter(MensajeCorreo.conversacion_id == lote.conversacion_id, MensajeCorreo.direccion == "ENTRANTE")
            .scalar()
        )
        if llegada and lote.fecha_creacion >= llegada:
            minutos.append((lote.fecha_creacion - llegada).total_seconds() / 60)
    return {
        "lotes": len(lotes), "pedidos": pedidos, "lotes_por_correo": len(minutos),
        "minutos_promedio": round(sum(minutos) / len(minutos), 1) if minutos else None,
    }


def indicadores(db: Session, periodo: str | None = None, desde: date | None = None, hasta: date | None = None) -> dict:
    """Indicadores del proyecto In.OE.1 a In.OE.4 del Charter en el periodo (C34-03). Recibe el periodo."""
    d, h = rango(periodo, desde, hasta)
    ini, fin = _limites(d, h)
    soles_km = _soles_por_km(db)

    rutas = _rutas_cerradas(db, ini, fin)
    km = [r.km_estimado for r in rutas if r.km_estimado]
    ahorro = sum(r.km_ahorrado or 0 for r in rutas)

    eventos = _eventos(db, ("ENTREGADO", "FALLIDO", "OBSERVADO", "CANCELADO"), ini, fin)
    entregados = {pid for pid, e, _ in eventos if e == "ENTREGADO"}
    fallidos = sum(1 for _, e, _ in eventos if e == "FALLIDO")
    observados = {pid for pid, e, _ in eventos if e == "OBSERVADO"}
    cancelados = {pid for pid, e, _ in eventos if e == "CANCELADO"}
    con_foto = con_gps = 0
    if entregados:
        evidencias = db.query(EvidenciaEntrega).filter(EvidenciaEntrega.pedido_id.in_(entregados)).all()
        con_foto = len({e.pedido_id for e in evidencias if e.url_foto})
        con_gps = len({e.pedido_id for e in evidencias if e.url_foto and e.latitud_longitud_captura})

    reclamado = (
        db.query(func.coalesce(func.sum(Reclamo.monto_reclamado), 0.0))
        .filter(Reclamo.creado_en >= ini, Reclamo.creado_en < fin).scalar() or 0.0
    )
    paradas = sum(len(r.detalles) for r in rutas if getattr(r, "detalles", None)) or 0
    costo_parada = (sum(km) * soles_km / paradas) if paradas else 0.0
    costo_reintentos = fallidos * costo_parada

    return {
        "desde": d.isoformat(), "hasta": h.isoformat(),
        "in_oe_1": _registro_de_lotes(db, ini, fin),
        "in_oe_2": {
            "rutas": len(rutas),
            "km_promedio_por_ruta": round(sum(km) / len(km), 2) if km else None,
            "km_ahorrados": round(ahorro, 1),
            "ahorro_porcentaje": round(ahorro / (sum(km) + ahorro) * 100, 1) if (sum(km) + ahorro) else None,
        },
        "in_oe_3": {
            "pedidos_perdidos": len(observados | cancelados),
            "observados_en_almacen": len(observados),
            "cancelados": len(cancelados),
            "entregas": len(entregados),
            "entregas_con_foto": con_foto,
            "entregas_con_foto_porcentaje": round(con_foto / len(entregados) * 100, 1) if entregados else None,
            "entregas_con_gps_porcentaje": round(con_gps / len(entregados) * 100, 1) if entregados else None,
        },
        "in_oe_4": {
            "reintentos": fallidos,
            "costo_reintentos_soles": round(costo_reintentos, 2),
            "monto_reclamado_soles": round(float(reclamado), 2),
            "perdidas_soles": round(costo_reintentos + float(reclamado), 2),
        },
    }


def excel_indicadores(db: Session, periodo: str | None = None, desde: date | None = None, hasta: date | None = None) -> tuple[bytes, str]:
    """Reporte de indicadores In.OE.1-4 y el detalle diario en Excel (C34-03). Recibe el periodo.
    Devuelve (bytes del .xlsx, nombre del archivo)."""
    from openpyxl import Workbook
    from openpyxl.styles import Font

    ind = indicadores(db, periodo, desde, hasta)
    tab = kpis(db, periodo, desde, hasta)
    vacio = lambda v: "—" if v is None else v  # noqa: E731
    o1, o2, o3, o4 = ind["in_oe_1"], ind["in_oe_2"], ind["in_oe_3"], ind["in_oe_4"]
    filas = [
        ("In.OE.1", "Tiempo de registro de un lote", vacio(o1["minutos_promedio"]), "min",
         f"Promedio de {o1['lotes_por_correo']} lotes llegados por correo: desde el correo hasta el registro. Lotes del periodo: {o1['lotes']} ({o1['pedidos']} pedidos)."),
        ("In.OE.2", "Distancia promedio por ruta", vacio(o2["km_promedio_por_ruta"]), "km",
         f"{o2['rutas']} rutas cerradas; ahorro {o2['km_ahorrados']} km ({vacio(o2['ahorro_porcentaje'])} %) frente al orden de carga."),
        ("In.OE.3", "Pedidos perdidos", o3["pedidos_perdidos"], "pedidos",
         f"Observados por faltante en almacén ({o3['observados_en_almacen']}) + cancelados ({o3['cancelados']})."),
        ("In.OE.3", "Entregas con foto", vacio(o3["entregas_con_foto_porcentaje"]), "%",
         f"{o3['entregas_con_foto']} de {o3['entregas']} entregas con foto POD; con GPS: {vacio(o3['entregas_con_gps_porcentaje'])} %."),
        ("In.OE.4", "Pérdidas", o4["perdidas_soles"], "S/",
         f"Reintentos {o4['reintentos']} × costo de combustible por parada (S/ {o4['costo_reintentos_soles']}) + monto reclamado en el Libro (S/ {o4['monto_reclamado_soles']})."),
        ("Tablero", "Cumplimiento", vacio(tab["cumplimiento"]), "%",
         f"{tab['entregados']} entregados de {tab['gestionados']} gestionados ({tab['fallidos']} fallidos)."),
        ("Tablero", "Ahorro de la flota", tab["ahorro_soles"], "S/", f"{tab['km_ahorrados']} km ahorrados × costo por km."),
        ("RNF-011", "Batería por hora de jornada", vacio(tab["bateria"]["por_hora"]), "% / h",
         f"{tab['bateria']['jornadas']} jornadas medidas desde la app; gasto promedio {vacio(tab['bateria']['gasto_promedio'])} % en {vacio(tab['bateria']['horas_promedio'])} h."),
    ]

    wb = Workbook()
    hoja = wb.active
    hoja.title = "Indicadores"
    hoja.append([f"Indicadores del proyecto GeoTrack · {ind['desde']} al {ind['hasta']}"])
    hoja["A1"].font = Font(bold=True, size=13)
    hoja.append([])
    hoja.append(["Código", "Indicador", "Valor", "Unidad", "Cómo se calcula"])
    for celda in hoja[3]:
        celda.font = Font(bold=True)
    for fila in filas:
        hoja.append(list(fila))
    for letra, ancho in zip("ABCDE", (10, 30, 12, 10, 90)):
        hoja.column_dimensions[letra].width = ancho

    diaria = wb.create_sheet("Detalle diario")
    diaria.append(["Día", "Entregados", "Fallidos"])
    for celda in diaria[1]:
        celda.font = Font(bold=True)
    for fila in tab["serie"]:
        diaria.append([fila["dia"], fila["entregados"], fila["fallidos"]])

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue(), f"indicadores_{ind['desde']}_{ind['hasta']}.xlsx"
