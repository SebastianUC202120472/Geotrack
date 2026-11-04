# Implementacion de las funciones de consulta. Cada una:
#   1. lee la API del nucleo con el token del usuario (solo GET),
#   2. resume los datos (el modelo recibe totales y una muestra, no tablas enormes),
#   3. arma los bloques visuales (tabla, grafico, enlace) con los datos reales.
# El enmascarado de DNI y telefonos se aplica despues, en el servicio de chat.
import asyncio
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import date
from urllib.parse import quote

from app.core.config import settings
from app.core.fechas import ahora_local, fecha_local_core, hoy_local, leer_fecha_core, texto_fecha_hora
from app.herramientas import bloques as B
from app.herramientas.catalogo import sin_tildes
from app.herramientas.cliente_core import ClienteCore, ErrorCore, SesionInvalida
from app.herramientas.zonas import zona_aproximada
from app.services.privacidad import enmascarar_correo

_PAGINA = 500
_MAX_MUESTRA = 10
_MAX_MOTIVOS = 20          # fallidos a los que se les busca el motivo (lo que cabe en una tabla)
_CONCURRENCIA_MOTIVOS = 5  # consultas de historial en paralelo hacia el nucleo
_SIN_MOTIVO = "Sin motivo registrado"
_RUTA_ACTIVA = ("CREADA", "EN_PROGRESO")
_RE_CODIGO = re.compile(r"^[A-Za-z0-9._-]{1,40}$")


@dataclass
class Contexto:
    """Datos de la peticion que necesitan las funciones: cliente del nucleo y rol del usuario."""
    core: ClienteCore
    rol: str


@dataclass
class Resultado:
    """Lo que devuelve una funcion: datos para el modelo y bloques para el widget."""
    datos: dict
    bloques: list = field(default_factory=list)


# ----------------------------------------------------------------------------- utilidades

def _normal(texto) -> str:
    """Texto en minusculas y sin tildes para comparar. Recibe el texto."""
    return sin_tildes(str(texto or "")).lower().strip()


def _contiene(valor, buscado) -> bool:
    """Dice si 'buscado' aparece en 'valor' sin importar mayusculas ni tildes. Recibe ambos textos."""
    return _normal(buscado) in _normal(valor)


def _hace(valor) -> str | None:
    """Convierte una marca del nucleo en 'hace N min/h/dias'. Recibe el valor crudo."""
    momento = leer_fecha_core(valor)
    if not momento:
        return None
    minutos = int((ahora_local() - momento).total_seconds() // 60)
    if minutos < 1:
        return "hace menos de un minuto"
    if minutos < 60:
        return f"hace {minutos} min"
    if minutos < 60 * 24:
        return f"hace {minutos // 60} h {minutos % 60} min"
    return f"hace {minutos // (60 * 24)} días"


def _presentar(args: dict, por_defecto: str = "texto") -> str:
    """Formato pedido para el resultado (texto, tabla o grafico). Recibe los argumentos."""
    return args.get("presentar") or por_defecto


def _sin_vacios(bloques: list) -> list:
    """Quita bloques nulos. Recibe la lista."""
    return [b for b in bloques if b]


async def _traer_pedidos(core: ClienteCore, **filtros) -> tuple[list, bool]:
    """Trae pedidos del nucleo por paginas hasta el tope configurado. Recibe filtros del endpoint."""
    todos: list = []
    tope = settings.ASISTENTE_MAX_PEDIDOS_CONSULTA
    skip = 0
    while skip < tope:
        pagina = await core.get("/pedidos/", {**filtros, "skip": skip, "limit": _PAGINA})
        todos.extend(pagina or [])
        if not pagina or len(pagina) < _PAGINA:
            return todos, False
        skip += _PAGINA
    return todos, True


# ----------------------------------------------------------------------------- resumen del dia

async def resumen_del_dia(ctx: Contexto, a: dict) -> Resultado:
    """Resumen de la operacion de hoy segun el rol. Recibe contexto y argumentos."""
    if ctx.rol == "almacen":
        return await _resumen_almacen(ctx)

    resumen, flota, auxilios, reportes, (entregados, truncado) = await asyncio.gather(
        ctx.core.get("/dashboard/resumen"),
        ctx.core.get("/dashboard/flota"),
        ctx.core.get("/incidencias", {"estado": "ABIERTA"}),
        ctx.core.get("/reportes/", {"estado": "ABIERTO"}),
        _traer_pedidos(ctx.core, estado="ENTREGADO"),
    )
    hoy = hoy_local()
    entregados_hoy = sum(1 for p in entregados if fecha_local_core(p.get("fecha_entrega")) == hoy)

    rutas_del_dia = [
        r for r in flota.get("rutas", [])
        if r.get("estado") in _RUTA_ACTIVA
        or fecha_local_core(r.get("fecha_creacion")) == hoy
        or fecha_local_core(r.get("fecha_fin")) == hoy
    ]
    activas = [r for r in rutas_del_dia if r.get("estado") in _RUTA_ACTIVA]
    por_estado = resumen.get("pedidos_por_estado", {})

    datos = {
        "fecha": hoy.strftime("%d/%m/%Y"),
        "entregados_hoy": entregados_hoy,
        "fallidos_en_rutas_del_dia": sum(r.get("fallidas", 0) for r in rutas_del_dia),
        "pedidos_en_ruta_ahora": por_estado.get("EN_RUTA", 0),
        "pedidos_asignados_sin_salir": por_estado.get("ASIGNADO", 0),
        "pedidos_listos_para_envio": por_estado.get("LISTO_PARA_ENVIO", 0),
        "pedidos_sin_ubicar": por_estado.get("GEOCODIFICACION_FALLIDA", 0),
        "rutas_activas": [
            {
                "ruta": r.get("nombre"),
                "conductor": r.get("conductor_nombre"),
                "avance_porcentaje": r.get("avance_porcentaje"),
                "entregadas": r.get("entregadas"),
                "fallidas": r.get("fallidas"),
                "pendientes": r.get("pendientes"),
            }
            for r in activas
        ],
        "auxilios_abiertos": [
            {
                "ruta": i.get("ruta_nombre"),
                "conductor": i.get("conductor_nombre"),
                "tipo": i.get("tipo"),
                "reportado": _hace(i.get("creado_en")),
                "ayuda_enviada": bool(i.get("ayuda_enviada_en")),
            }
            for i in auxilios
        ],
        "reportes_de_falla_abiertos": len(reportes),
        # Los pendientes de las rutas activas son los mismos pedidos EN_RUTA: se envian una sola
        # vez (pedidos_en_ruta_ahora) y, por ruta, en rutas_activas, para que no se repitan.
        "nota": "Los fallidos del día se cuentan en las rutas de hoy: el pedido no guarda la hora exacta del fallo. "
                "pedidos_en_ruta_ahora ya incluye las paradas pendientes de las rutas activas: no lo repitas como otra cifra.",
    }
    if truncado:
        datos["advertencia"] = "Había demasiados pedidos entregados para revisarlos todos; el número de entregados hoy puede ser mayor."
    return Resultado(datos, _sin_vacios([B.enlace("Abrir el dashboard", "/panel")]))


async def _resumen_almacen(ctx: Contexto) -> Resultado:
    """Resumen del dia para el personal de almacen. Recibe el contexto."""
    recojos, observados, retornos = await asyncio.gather(
        ctx.core.get("/almacen/recojos"),
        ctx.core.get("/almacen/observados"),
        ctx.core.get("/almacen/retornos/rutas"),
    )
    datos = {
        "fecha": hoy_local().strftime("%d/%m/%Y"),
        "recojos_por_estado": dict(Counter(r.get("estado") for r in recojos)),
        "pedidos_observados": len(observados),
        "rutas_con_retornos": len(retornos),
        "paquetes_por_retornar": sum((r.get("conteo") or {}).get("faltantes", 0) for r in retornos),
    }
    return Resultado(datos, _sin_vacios([
        B.enlace("Abrir Ingreso a Almacén", "/panel/almacen"),
        B.enlace("Ver retornos", "/panel/almacen/retornos"),
    ]))


# ----------------------------------------------------------------------------- pedidos

def _fila_pedido(p: dict) -> dict:
    """Datos de un pedido que se muestran al modelo. Recibe el pedido del nucleo."""
    return {
        "codigo": p.get("codigo"),
        "referencia": p.get("referencia_externa"),
        "cliente": p.get("cliente_origen"),
        "destinatario": p.get("nombre_destinatario"),
        "dni_destinatario": p.get("dni_destinatario"),
        "distrito": p.get("distrito"),
        "direccion": p.get("direccion_destino"),
        "estado": p.get("estado"),
        "creado": texto_fecha_hora(p.get("fecha_creacion")),
        "entregado": texto_fecha_hora(p.get("fecha_entrega")),
        "ruta": p.get("ruta_nombre"),
        "conductor": p.get("conductor_nombre"),
    }


def _en_rango(dia: date | None, desde: str | None, hasta: str | None) -> bool:
    """Dice si una fecha cae entre desde y hasta (inclusive). Recibe la fecha y los limites ISO."""
    if dia is None:
        return False
    if desde and dia < date.fromisoformat(desde):
        return False
    if hasta and dia > date.fromisoformat(hasta):
        return False
    return True


def _texto_periodo(desde: str | None, hasta: str | None, campo: str | None = None) -> str:
    """Describe el periodo consultado para que el modelo no invente uno ("hoy"). Recibe limites ISO y campo."""
    if not desde and not hasta:
        return "Sin filtro de fecha: incluye todos los registros que hoy están en ese estado, de cualquier día."

    def fmt(iso: str) -> str:
        """Fecha ISO a dd/mm/aaaa. Recibe la fecha."""
        return date.fromisoformat(iso).strftime("%d/%m/%Y")

    if desde and hasta:
        rango = f"del {fmt(desde)} al {fmt(hasta)}" if desde != hasta else f"el {fmt(desde)}"
    else:
        rango = f"desde el {fmt(desde)}" if desde else f"hasta el {fmt(hasta)}"
    return f"{rango.capitalize()}" + (f", según la {campo}." if campo else ".")


async def _motivos_fallo(core: ClienteCore, pedidos: list) -> dict:
    """Motivo de fallo de los primeros pedidos FALLIDO. Recibe el cliente y los pedidos.

    El listado de pedidos del nucleo no trae el motivo: solo el historial de cada pedido.
    Por eso se consulta un numero acotado de pedidos, con pocas consultas a la vez.
    """
    codigos = [
        p["codigo"] for p in pedidos
        if p.get("estado") == "FALLIDO" and isinstance(p.get("codigo"), str) and _RE_CODIGO.match(p["codigo"])
    ][:_MAX_MOTIVOS]
    semaforo = asyncio.Semaphore(_CONCURRENCIA_MOTIVOS)

    async def uno(codigo: str):
        async with semaforo:
            try:
                h = await core.get(f"/dashboard/pedidos/{quote(codigo, safe='')}/historial")
            except SesionInvalida:
                raise
            except ErrorCore:
                return codigo, None
            return codigo, (h or {}).get("motivo_fallo")

    return dict(await asyncio.gather(*(uno(c) for c in codigos)))


async def buscar_pedidos(ctx: Contexto, a: dict) -> Resultado:
    """Busca, filtra y cuenta pedidos. Recibe contexto y filtros validados."""
    codigo, cliente, texto = a.get("codigo"), a.get("cliente"), a.get("texto")
    estado = a.get("estado")
    busqueda = codigo or cliente or texto
    pedidos, truncado = await _traer_pedidos(ctx.core, busqueda=busqueda, estado=estado)

    if codigo:
        exactos = [
            p for p in pedidos
            if _normal(p.get("codigo")) == _normal(codigo) or _normal(p.get("referencia_externa")) == _normal(codigo)
        ]
        pedidos = exactos or pedidos
    if cliente:
        pedidos = [p for p in pedidos if _contiene(p.get("cliente_origen"), cliente)]
    if texto and texto != busqueda:
        pedidos = [
            p for p in pedidos
            if any(_contiene(p.get(c), texto) for c in ("codigo", "cliente_origen", "direccion_destino", "distrito"))
        ]
    if a.get("dni"):
        dni = re.sub(r"\D", "", a["dni"])
        pedidos = [p for p in pedidos if re.sub(r"\D", "", p.get("dni_destinatario") or "") == dni]
    if a.get("distrito"):
        pedidos = [p for p in pedidos if _contiene(p.get("distrito"), a["distrito"])]

    campo = a.get("fecha_de") or ("entrega" if estado == "ENTREGADO" else "creacion")
    clave_fecha = "fecha_entrega" if campo == "entrega" else "fecha_creacion"
    if a.get("desde") or a.get("hasta"):
        pedidos = [p for p in pedidos if _en_rango(fecha_local_core(p.get(clave_fecha)), a.get("desde"), a.get("hasta"))]

    conteo = Counter(p.get("estado") for p in pedidos)
    motivos = await _motivos_fallo(ctx.core, pedidos) if conteo.get("FALLIDO") else {}

    def fila(p: dict) -> dict:
        f = _fila_pedido(p)
        if p.get("codigo") in motivos:
            f["motivo_fallo"] = motivos[p["codigo"]] or _SIN_MOTIVO
        return f

    datos = {
        "total": len(pedidos),
        "filtros_aplicados": {k: v for k, v in a.items() if k not in ("presentar", "agrupar_por")},
        "conteo_por_estado": dict(conteo),
        # Conteos sobre TODOS los pedidos encontrados: el modelo debe usar estos y nunca contar la muestra.
        "conteo_por_cliente": dict(Counter((p.get("cliente_origen") or "Sin dato") for p in pedidos).most_common(_MAX_MUESTRA)),
        "conteo_por_distrito": dict(Counter((p.get("distrito") or "Sin dato") for p in pedidos).most_common(_MAX_MUESTRA)),
        "muestra": [fila(p) for p in pedidos[:_MAX_MUESTRA]],
    }
    if motivos:
        datos["motivos_de_fallo"] = dict(Counter(m or _SIN_MOTIVO for m in motivos.values()).most_common())
        if conteo["FALLIDO"] > len(motivos):
            datos["nota_motivos"] = (
                f"Motivos revisados en {len(motivos)} de {conteo['FALLIDO']} pedidos fallidos (los más recientes)."
            )
    datos["periodo"] = _texto_periodo(
        a.get("desde"), a.get("hasta"), "fecha de entrega" if campo == "entrega" else "fecha de creación del pedido"
    )
    if estado == "FALLIDO":
        datos["nota_fecha"] = "El sistema no guarda el día exacto del fallo: no digas que fallaron 'hoy' salvo que el periodo lo indique."
    if len(pedidos) > _MAX_MUESTRA:
        datos["nota_muestra"] = (
            f"La muestra trae solo {_MAX_MUESTRA} de {len(pedidos)} pedidos (los más recientes): "
            "no cuentes sobre ella; para totales usa total y los campos conteo_*."
        )
    if truncado:
        datos["advertencia"] = f"La consulta llegó al tope de {settings.ASISTENTE_MAX_PEDIDOS_CONSULTA} pedidos revisados; los totales pueden ser mayores."

    agrupacion = None
    if a.get("agrupar_por"):
        agrupacion = _agrupar(pedidos, a["agrupar_por"], clave_fecha)
        datos["agrupacion"] = {"por": a["agrupar_por"], "valores": agrupacion}

    bloques = []
    presentar = _presentar(a)
    # Respaldo: si se consultan fallidos con su motivo, la lista va en la tabla del servidor
    # aunque el modelo pida solo texto (el texto debe ser un resumen breve, sin tablas).
    if presentar == "texto" and motivos and estado == "FALLIDO":
        presentar = "tabla"
    if presentar == "tabla":
        columnas = ["Código", "Cliente", "Distrito", "Estado", "Creado", "Conductor"]
        filas = [[p.get("codigo"), p.get("cliente_origen"), p.get("distrito"), p.get("estado"),
                  texto_fecha_hora(p.get("fecha_creacion")), p.get("conductor_nombre")] for p in pedidos]
        if motivos:
            columnas.append("Motivo de fallo")
            for f, p in zip(filas, pedidos):
                f.append((motivos.get(p.get("codigo")) or _SIN_MOTIVO) if p.get("estado") == "FALLIDO" else None)
        bloques.append(B.tabla("Pedidos encontrados", columnas, filas))
    elif presentar == "grafico":
        if motivos and estado == "FALLIDO" and not a.get("agrupar_por"):
            bloques.append(B.grafico("Pedidos fallidos por motivo", list(datos["motivos_de_fallo"].items()), "torta"))
        else:
            serie = agrupacion or dict(conteo)
            por = a.get("agrupar_por") or "estado"
            bloques.append(B.grafico(f"Pedidos por {por}", list(serie.items()), "barras"))

    distritos = {p.get("distrito") for p in pedidos if p.get("distrito")}
    bloques.append(B.enlace(
        "Ver en Pedidos",
        "/panel/pedidos",
        {"estado": estado, "distrito": distritos.pop() if a.get("distrito") and len(distritos) == 1 else None},
    ))
    return Resultado(datos, _sin_vacios(bloques))


def _agrupar(pedidos: list, por: str, clave_fecha: str) -> dict:
    """Cuenta pedidos por estado, distrito, cliente o dia. Recibe pedidos, criterio y campo de fecha."""
    if por == "dia":
        claves = [(fecha_local_core(p.get(clave_fecha)) or "sin fecha") for p in pedidos]
        conteo = Counter(str(c) for c in claves)
        return dict(sorted(conteo.items()))
    campo = {"estado": "estado", "distrito": "distrito", "cliente": "cliente_origen"}[por]
    return dict(Counter((p.get(campo) or "Sin dato") for p in pedidos).most_common())


async def trazabilidad_pedido(ctx: Contexto, a: dict) -> Resultado:
    """Linea de tiempo de un pedido por su codigo. Recibe contexto y {codigo}."""
    codigo = a["codigo"].strip().upper().replace(" ", "")
    if not _RE_CODIGO.match(codigo):
        return Resultado({"error": "El código de pedido no tiene un formato válido."})
    h, reportes = await asyncio.gather(
        ctx.core.get(f"/dashboard/pedidos/{quote(codigo, safe='')}/historial"),
        ctx.core.get("/reportes/", {"estado": None}),
        return_exceptions=True,
    )
    if isinstance(h, BaseException):
        raise h
    # Sin la lista de reportes la trazabilidad igual sirve: solo cambia el boton.
    reportes = [] if isinstance(reportes, BaseException) else reportes
    eventos = [
        {
            "fecha": texto_fecha_hora(e.get("fecha")),
            "evento": e.get("evento"),
            "descripcion": e.get("descripcion"),
            "realizado_por": e.get("realizado_por"),
        }
        for e in h.get("eventos", [])
    ]
    datos = {
        "codigo": h.get("codigo"),
        "cliente": h.get("cliente_origen"),
        "distrito": h.get("distrito"),
        "direccion": h.get("direccion_destino"),
        "estado_actual": h.get("estado_actual"),
        "ruta": h.get("ruta_asignada"),
        "conductor": h.get("conductor_asignado"),
        "parada_numero": h.get("secuencia"),
        "motivo_fallo": h.get("motivo_fallo"),
        "tiene_foto_de_entrega": bool(h.get("url_evidencia")),
        "eventos": eventos,
    }
    bloques = []
    if _presentar(a, "tabla") != "texto" and eventos:
        bloques.append(B.tabla(
            f"Trazabilidad de {h.get('codigo') or codigo}",
            ["Fecha", "Evento", "Detalle", "Por"],
            [[e["fecha"], e["evento"], e["descripcion"], e["realizado_por"]] for e in eventos],
        ))
    # El boton de reportes solo si el pedido tiene alguno (si no, abre una lista vacia).
    if any(_normal(r.get("pedido_codigo")) == _normal(codigo) for r in reportes or []):
        bloques.append(B.enlace("Ver reportes del pedido", "/panel/reportes", {"pedido": h.get("codigo") or codigo}))
    else:
        bloques.append(B.enlace("Ver en Pedidos", "/panel/pedidos",
                                {"estado": h.get("estado_actual"), "distrito": h.get("distrito")}))
    return Resultado(datos, _sin_vacios(bloques))


# ----------------------------------------------------------------------------- rutas y conductores

async def estado_rutas(ctx: Contexto, a: dict) -> Resultado:
    """Rutas con su avance, filtradas por nombre, conductor o solo activas. Recibe contexto y filtros."""
    flota = await ctx.core.get("/dashboard/flota")
    rutas = flota.get("rutas", [])
    # Si se pide una ruta o un conductor concreto se busca en todas (una ruta finalizada tambien vale);
    # sin filtros, por defecto solo las que estan en curso.
    solo_activas = a.get("solo_activas", not (a.get("nombre") or a.get("conductor")))
    if solo_activas:
        rutas = [r for r in rutas if r.get("estado") in _RUTA_ACTIVA]
    if a.get("nombre"):
        rutas = [r for r in rutas if _contiene(r.get("nombre"), a["nombre"])]
    if a.get("conductor"):
        rutas = [r for r in rutas if _contiene(r.get("conductor_nombre"), a["conductor"])]

    filas = [
        {
            "ruta": r.get("nombre"),
            "estado": r.get("estado"),
            "conductor": r.get("conductor_nombre"),
            "placa": r.get("vehiculo_placa"),
            "paradas": r.get("total_paradas"),
            "entregadas": r.get("entregadas"),
            "fallidas": r.get("fallidas"),
            "pendientes": r.get("pendientes"),
            "avance_porcentaje": r.get("avance_porcentaje"),
            "creada": texto_fecha_hora(r.get("fecha_creacion")),
        }
        for r in rutas
    ]
    datos = {"total": len(filas), "solo_activas": solo_activas, "rutas": filas[:25]}
    bloques = []
    presentar = _presentar(a)
    if presentar == "tabla":
        bloques.append(B.tabla(
            "Rutas",
            ["Ruta", "Conductor", "Avance %", "Entregadas", "Fallidas", "Pendientes"],
            [[f["ruta"], f["conductor"], f["avance_porcentaje"], f["entregadas"], f["fallidas"], f["pendientes"]] for f in filas],
        ))
    elif presentar == "grafico":
        bloques.append(B.grafico("Avance por ruta (%)", [(f["ruta"], f["avance_porcentaje"] or 0) for f in filas]))
    bloques.append(B.enlace("Ver seguimiento de conductores", "/panel/seguimiento-conductores"))
    return Resultado(datos, _sin_vacios(bloques))


async def ubicacion_conductores(ctx: Contexto, a: dict) -> Resultado:
    """Ultima ubicacion de los conductores con zona aproximada. Recibe contexto y {nombre}."""
    ruta_ubicaciones = "/almacen/flota/ubicaciones-recojo" if ctx.rol == "almacen" else "/dashboard/flota/ubicaciones"
    ubicaciones, conductores = await asyncio.gather(ctx.core.get(ruta_ubicaciones), ctx.core.get("/conductores/"))
    nombre = a.get("nombre")
    if nombre:
        ubicaciones = [u for u in ubicaciones if _contiene(u.get("conductor"), nombre)]
        conductores = [c for c in conductores if _contiene(c.get("nombre"), nombre)]

    con_senal, en_ruta_sin_gps = [], []
    for u in ubicaciones:
        pendientes = [p for p in u.get("paradas", []) if p.get("estado") not in ("ENTREGADO", "FALLIDO")]
        proxima = min(pendientes, key=lambda p: p.get("secuencia") or 9999, default=None)
        base = {
            "conductor": u.get("conductor"),
            "ruta": u.get("ruta"),
            "pausado_por_auxilio": u.get("pausado", False),
            "paradas_pendientes": len(pendientes),
            "proxima_parada": {
                "numero": proxima.get("secuencia"),
                "destinatario": proxima.get("destinatario"),
                "zona_aproximada": zona_aproximada(proxima.get("latitud"), proxima.get("longitud")),
            } if proxima else None,
        }
        # Con ruta pero sin ningun punto enviado: NO tiene ubicacion. Se separa para que el modelo
        # no lo cuente como "en linea" por estar en la lista de ubicaciones.
        if u.get("latitud") is None or u.get("longitud") is None:
            en_ruta_sin_gps.append({**base, "situacion": "en ruta, pero la app aún no envió su ubicación (desconectado)"})
            continue
        en_linea = bool(u.get("en_linea", False))
        con_senal.append({
            **base,
            "senal": "en línea" if en_linea else f"desconectado (última señal {_hace(u.get('actualizado_en')) or 'sin dato'})",
            "en_linea": en_linea,
            "zona_aproximada": zona_aproximada(u.get("latitud"), u.get("longitud")),
            "ultima_senal": texto_fecha_hora(u.get("actualizado_en")),
            "hace": _hace(u.get("actualizado_en")),
            "latitud": round(u["latitud"], 4),
            "longitud": round(u["longitud"], 4),
        })

    nombres_con_senal = {_normal(c["conductor"]) for c in con_senal + en_ruta_sin_gps}
    sin_senal = en_ruta_sin_gps + [
        {
            "conductor": c.get("nombre"),
            "situacion": "en ruta pero sin señal de ubicación reciente" if c.get("en_ruta") else "sin ruta activa ahora",
            "cuenta_activa": c.get("estado", True),
            "placa": (c.get("vehiculo") or {}).get("placa"),
        }
        for c in conductores
        if _normal(c.get("nombre")) not in nombres_con_senal and (nombre or c.get("en_ruta"))
    ]
    datos = {
        "conductores_con_ubicacion": con_senal,
        "conductores_sin_ubicacion": sin_senal[:15],
        "en_linea_ahora": sum(1 for c in con_senal if c["en_linea"]),
        "nota": "La zona es aproximada (distrito más cercano al último punto enviado por la app). "
                "Solo están en línea los que tienen senal 'en línea'; los demás están desconectados.",
    }
    if nombre and not con_senal and not sin_senal:
        datos["resultado"] = f"No hay ningún conductor que coincida con '{nombre}'."

    bloques = []
    if _presentar(a) == "tabla":
        bloques.append(B.tabla(
            "Ubicación de conductores",
            ["Conductor", "Ruta", "Zona aprox.", "Última señal", "Pendientes"],
            [[c["conductor"], c["ruta"], c["zona_aproximada"], c["hace"], c["paradas_pendientes"]] for c in con_senal],
        ))
    destino = "/panel/almacen/mapa" if ctx.rol == "almacen" else "/panel/seguimiento-conductores"
    bloques.append(B.enlace("Ver en el mapa", destino))
    return Resultado(datos, _sin_vacios(bloques))


# ----------------------------------------------------------------------------- incidencias

async def auxilios_mecanicos(ctx: Contexto, a: dict) -> Resultado:
    """Auxilios mecanicos por estado y conductor. Recibe contexto y filtros."""
    estado = a.get("estado", "ABIERTA")
    lista = await ctx.core.get("/incidencias", {"estado": None if estado == "TODAS" else estado})
    if a.get("conductor"):
        lista = [i for i in lista if _contiene(i.get("conductor_nombre"), a["conductor"])]
    filas = [
        {
            "codigo": i.get("codigo"),
            "ruta": i.get("ruta_nombre"),
            "conductor": i.get("conductor_nombre"),
            "placa": i.get("vehiculo_placa"),
            "tipo": i.get("tipo"),
            "descripcion": i.get("descripcion"),
            "estado": i.get("estado"),
            "reportado": texto_fecha_hora(i.get("creado_en")),
            "hace": _hace(i.get("creado_en")),
            "zona_aproximada": zona_aproximada(i.get("latitud"), i.get("longitud")),
            "ayuda_enviada": bool(i.get("ayuda_enviada_en")),
            "ayuda_detalle": i.get("ayuda_detalle"),
            "conductor_puede_solucionarlo": i.get("puede_solucionar_solo", False),
        }
        for i in lista
    ]
    datos = {"estado_consultado": estado, "total": len(filas), "auxilios": filas[:20]}
    bloques = []
    presentar = _presentar(a)
    if presentar == "tabla":
        bloques.append(B.tabla(
            "Auxilios mecánicos",
            ["Código", "Ruta", "Conductor", "Placa", "Estado", "Reportado"],
            [[f["codigo"], f["ruta"], f["conductor"], f["placa"], f["estado"], f["hace"]] for f in filas],
        ))
    elif presentar == "grafico":
        bloques.append(B.grafico("Auxilios por conductor", list(Counter(f["conductor"] for f in filas).items())))
    bloques.append(B.enlace("Abrir Auxilio mecánico", "/panel/auxilio", {"estado": "ABIERTA" if estado == "ABIERTA" else None}))
    return Resultado(datos, _sin_vacios(bloques))


async def reportes_falla(ctx: Contexto, a: dict) -> Resultado:
    """Reportes de falla de pedidos. Recibe contexto y filtros."""
    estado = a.get("estado", "ABIERTO")
    lista = await ctx.core.get("/reportes/", {"estado": None if estado == "TODOS" else estado})
    if a.get("pedido"):
        lista = [r for r in lista if _normal(r.get("pedido_codigo")) == _normal(a["pedido"])]
    filas = [
        {
            "pedido": r.get("pedido_codigo"),
            "conductor": r.get("conductor_nombre"),
            "motivo": r.get("motivo"),
            "descripcion": r.get("descripcion"),
            "estado": r.get("estado"),
            "creado": texto_fecha_hora(r.get("creado_en")),
            "respuesta": r.get("respuesta"),
            "accion": r.get("accion"),
        }
        for r in lista
    ]
    datos = {
        "estado_consultado": estado,
        "periodo": _texto_periodo(None, None),
        "total": len(filas),
        "por_motivo": dict(Counter(f["motivo"] for f in filas).most_common()),
        "reportes": filas[:15],
    }
    bloques = []
    presentar = _presentar(a)
    if presentar == "tabla":
        bloques.append(B.tabla(
            "Reportes de falla",
            ["Pedido", "Conductor", "Motivo", "Detalle", "Estado", "Creado"],
            [[f["pedido"], f["conductor"], f["motivo"], f["descripcion"], f["estado"], f["creado"]] for f in filas],
        ))
    elif presentar == "grafico":
        bloques.append(B.grafico("Reportes por motivo", list(datos["por_motivo"].items()), "torta"))
    bloques.append(B.enlace(
        "Abrir Reportes de pedido",
        "/panel/reportes",
        {"estado": "ABIERTO" if estado == "ABIERTO" else None, "pedido": a.get("pedido")},
    ))
    return Resultado(datos, _sin_vacios(bloques))


# ----------------------------------------------------------------------------- bandeja

async def solicitudes_bandeja(ctx: Contexto, a: dict) -> Resultado:
    """Conversaciones de la Bandeja o el extracto de una de ellas. Recibe contexto y filtros."""
    enlace = B.enlace("Abrir la Bandeja", "/panel/bandeja")
    if a.get("conversacion_id"):
        c = await ctx.core.get(f"/correos/conversaciones/{a['conversacion_id']}")
        mensajes = (c.get("mensajes") or [])[-3:]
        datos = {
            "id": c.get("id"),
            "contraparte": c.get("contraparte_nombre") or enmascarar_correo(c.get("contraparte_email")),
            "asunto": c.get("asunto"),
            "estado": c.get("estado"),
            "ultimos_mensajes": [
                {
                    "direccion": m.get("direccion"),
                    "remitente": enmascarar_correo(m.get("remitente")),
                    "fecha": texto_fecha_hora(m.get("fecha")),
                    "asunto": m.get("asunto"),
                    "extracto": (m.get("cuerpo") or "")[:500],
                    "adjuntos": len(m.get("adjuntos") or []),
                }
                for m in mensajes
            ],
        }
        return Resultado(datos, _sin_vacios([enlace]))

    estado = a.get("estado", "PENDIENTE")
    lista = await ctx.core.get("/correos/conversaciones")
    if estado != "TODAS":
        lista = [c for c in lista if c.get("estado") == estado]
    filas = [
        {
            "id": c.get("id"),
            "contraparte": c.get("contraparte_nombre") or enmascarar_correo(c.get("contraparte_email")),
            "asunto": c.get("asunto"),
            "estado": c.get("estado"),
            "no_leidos": c.get("no_leidos"),
            "ultimo_mensaje": texto_fecha_hora(c.get("ultimo_mensaje_en")),
        }
        for c in lista
    ]
    datos = {"estado_consultado": estado, "total": len(filas), "conversaciones": filas[:15]}
    bloques = []
    if _presentar(a) == "tabla":
        bloques.append(B.tabla(
            "Bandeja de solicitudes",
            ["Contraparte", "Asunto", "Estado", "No leídos", "Último"],
            [[f["contraparte"], f["asunto"], f["estado"], f["no_leidos"], f["ultimo_mensaje"]] for f in filas],
        ))
    bloques.append(enlace)
    return Resultado(datos, _sin_vacios(bloques))


# ----------------------------------------------------------------------------- almacen

async def retornos_almacen(ctx: Contexto, a: dict) -> Resultado:
    """Rutas con pedidos fallidos por retornar, o el detalle de una. Recibe contexto y {ruta_id}."""
    # El admin no tiene las pantallas de almacen en su menu: se le abre Pedidos ya filtrado.
    if ctx.rol == "almacen":
        enlace = B.enlace("Abrir Retornos de ruta", "/panel/almacen/retornos")
    else:
        enlace = B.enlace("Ver fallidos en Pedidos", "/panel/pedidos", {"estado": "FALLIDO"})
    ruta_id = a.get("ruta_id")
    if not ruta_id and a.get("ruta"):
        # El usuario suele decir el nombre ("Ruta Surquillo"): se busca su id en la lista.
        lista = await ctx.core.get("/almacen/retornos/rutas") or []
        coinciden = [r for r in lista if _contiene(r.get("nombre"), a["ruta"]) or _normal(r.get("codigo")) == _normal(a["ruta"])]
        if len(coinciden) != 1:
            return Resultado({
                "error": "No hay una ruta con retornos con ese nombre." if not coinciden
                else "Hay varias rutas con ese nombre; pide al usuario que elija una.",
                "rutas": [r.get("nombre") for r in coinciden[:10]],
            }, _sin_vacios([enlace]))
        ruta_id = coinciden[0].get("ruta_id")
    if ruta_id:
        r = await ctx.core.get(f"/almacen/retornos/rutas/{int(ruta_id)}")
        datos = {
            "ruta": r.get("nombre"),
            "codigo": r.get("codigo"),
            "conteo": r.get("conteo"),
            "fallidos": [
                {
                    "codigo": f.get("codigo"),
                    "cliente": f.get("cliente_origen"),
                    "destinatario": f.get("nombre_destinatario"),
                    "retornado": texto_fecha_hora(f.get("retornado_en")) or "aún no",
                }
                for f in r.get("fallidos", [])
            ][:25],
        }
        bloques = []
        if _presentar(a, "tabla") != "texto" and datos["fallidos"]:
            bloques.append(B.tabla(
                f"Paquetes de {r.get('nombre') or 'la ruta'}",
                ["Código", "Cliente", "Destinatario", "Retornado"],
                [[f["codigo"], f["cliente"], f["destinatario"], f["retornado"]] for f in datos["fallidos"]],
            ))
        bloques.append(enlace)
        return Resultado(datos, _sin_vacios(bloques))

    lista = await ctx.core.get("/almacen/retornos/rutas")
    filas = [
        {"ruta_id": r.get("ruta_id"), "ruta": r.get("nombre"), "estado": r.get("estado"), **(r.get("conteo") or {})}
        for r in lista
    ]
    datos = {
        "rutas": filas[:25],
        "total_rutas": len(filas),
        "paquetes_por_retornar": sum(f.get("faltantes", 0) for f in filas),
    }
    bloques = []
    if _presentar(a) == "tabla":
        bloques.append(B.tabla(
            "Retornos al almacén",
            ["Ruta", "Esperados", "Retornados", "Faltan"],
            [[f["ruta"], f.get("esperados"), f.get("retornados"), f.get("faltantes")] for f in filas],
        ))
    bloques.append(enlace)
    return Resultado(datos, _sin_vacios(bloques))


async def pedidos_observados(ctx: Contexto, a: dict) -> Resultado:
    """Pedidos observados (faltantes al ingresar). Recibe contexto y {cliente}."""
    lista = await ctx.core.get("/almacen/observados")
    if a.get("cliente"):
        lista = [o for o in lista if _contiene(o.get("cliente"), a["cliente"])]
    filas = [
        {
            "codigo": o.get("codigo"),
            "referencia": o.get("referencia"),
            "cliente": o.get("cliente"),
            "destinatario": o.get("destinatario"),
            "lote": o.get("lote"),
            "dias_observado": o.get("dias"),
        }
        for o in lista
    ]
    datos = {"total": len(filas), "por_cliente": dict(Counter(f["cliente"] for f in filas)), "pedidos": filas[:20]}
    bloques = []
    presentar = _presentar(a)
    if presentar == "tabla":
        bloques.append(B.tabla(
            "Pedidos observados",
            ["Código", "Cliente", "Lote", "Días"],
            [[f["codigo"], f["cliente"], f["lote"], f["dias_observado"]] for f in filas],
        ))
    elif presentar == "grafico":
        bloques.append(B.grafico("Observados por cliente", list(datos["por_cliente"].items())))
    if ctx.rol == "almacen":
        bloques.append(B.enlace("Abrir Pedidos observados", "/panel/almacen/observados"))
    else:
        bloques.append(B.enlace("Ver observados en Pedidos", "/panel/pedidos", {"estado": "OBSERVADO"}))
    return Resultado(datos, _sin_vacios(bloques))


async def recojos_almacen(ctx: Contexto, a: dict) -> Resultado:
    """Solicitudes de recojo con su conciliacion. Recibe contexto y filtros."""
    estado = a.get("estado")
    lista = await ctx.core.get("/almacen/recojos", {"estado": estado.upper() if estado else None})
    if a.get("cliente"):
        lista = [r for r in lista if _contiene(r.get("cliente_origen"), a["cliente"])]
    filas = [
        {
            "codigo": r.get("codigo"),
            "cliente": r.get("cliente_origen"),
            "estado": r.get("estado"),
            "cantidad_declarada": r.get("cantidad_declarada"),
            **(r.get("conteo") or {}),
        }
        for r in lista
    ]
    datos = {"total": len(filas), "por_estado": dict(Counter(f["estado"] for f in filas)), "recojos": filas[:20]}
    bloques = []
    if _presentar(a) == "tabla":
        bloques.append(B.tabla(
            "Recojos",
            ["Código", "Cliente", "Estado", "Esperados", "Listos", "Observados"],
            [[f["codigo"], f["cliente"], f["estado"], f.get("esperados"), f.get("listos"), f.get("observados")] for f in filas],
        ))
    bloques.append(B.enlace("Abrir Ingreso a Almacén", "/panel/almacen"))
    return Resultado(datos, _sin_vacios(bloques))


# ----------------------------------------------------------------------------- clientes

async def avance_por_cliente(ctx: Contexto, a: dict) -> Resultado:
    """Avance acumulado por empresa cliente. Recibe contexto y {cliente}."""
    lista = await ctx.core.get("/dashboard/clientes")
    if a.get("cliente"):
        lista = [c for c in lista if _contiene(c.get("cliente"), a["cliente"])]
    datos = {"total_clientes": len(lista), "clientes": lista[:20]}
    bloques = []
    presentar = _presentar(a)
    if presentar == "tabla":
        bloques.append(B.tabla(
            "Avance por cliente",
            ["Cliente", "Total", "Entregados", "Fallidos", "En proceso", "Pendientes"],
            [[c.get("cliente"), c.get("total"), c.get("entregados"), c.get("fallidos"), c.get("en_proceso"), c.get("pendientes")] for c in lista],
        ))
    elif presentar == "grafico":
        bloques.append(B.grafico("Pedidos entregados por cliente", [(c.get("cliente"), c.get("entregados", 0)) for c in lista]))
    bloques.append(B.enlace("Abrir el dashboard", "/panel"))
    return Resultado(datos, _sin_vacios(bloques))


FUNCIONES = {
    "resumen_del_dia": resumen_del_dia,
    "buscar_pedidos": buscar_pedidos,
    "trazabilidad_pedido": trazabilidad_pedido,
    "estado_rutas": estado_rutas,
    "ubicacion_conductores": ubicacion_conductores,
    "auxilios_mecanicos": auxilios_mecanicos,
    "reportes_falla": reportes_falla,
    "solicitudes_bandeja": solicitudes_bandeja,
    "retornos_almacen": retornos_almacen,
    "pedidos_observados": pedidos_observados,
    "recojos_almacen": recojos_almacen,
    "avance_por_cliente": avance_por_cliente,
}
