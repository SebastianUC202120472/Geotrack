"""Construye los mensajes de cada aviso. Cada evento es una funcion decorada: dar de alta
un aviso nuevo no exige tocar los demas (principio abierto/cerrado)."""
import re
from collections.abc import Callable
from dataclasses import replace

from app.repositories import notificacion_automatica_repository as repo
from app.services.notificaciones_automaticas import destinatarios as dest
from app.services.notificaciones_automaticas.modelos import Canal, Destinatario, Mensaje, Prioridad

_CONSTRUCTORES: dict[str, Callable[[dict], list[Mensaje]]] = {}
_VARIABLE = re.compile(r"\{(\w+)\}")


def registrar(evento: str):
    """Da de alta el constructor de un evento sin modificar este archivo."""
    def _wrap(fn):
        """Guarda la funcion como constructor del evento. Recibe la funcion."""
        _CONSTRUCTORES[evento] = fn
        return fn
    return _wrap


def construir_mensaje(evento: str, contexto: dict, db=None) -> list[Mensaje]:
    """Devuelve los mensajes de un evento a partir de su contexto; vacio si no existe.
    Con base de datos aplica lo configurado en el panel: no envia a quien pidio STOP, omite
    los avisos cuya plantilla esta apagada y usa el texto editado de la plantilla."""
    fn = _CONSTRUCTORES.get(evento)
    mensajes = fn(contexto, db) if fn else []
    if db is None or not hasattr(db, "query"):
        return mensajes
    salida, variables = [], None
    for m in mensajes:
        if repo.esta_de_baja(db, m.canal.value, m.destinatario.valor):
            continue
        plantilla = repo.obtener_plantilla_evento(db, m.evento, m.canal.value)
        if plantilla is not None:
            if not plantilla.activo:
                continue
            variables = variables if variables is not None else _variables(evento, contexto)
            asunto = _rellenar(plantilla.asunto, variables) if (plantilla.asunto and m.canal == Canal.CORREO) else m.asunto
            m = replace(m, cuerpo=_rellenar(plantilla.cuerpo, variables), asunto=asunto)
        salida.append(m)
    return salida


def _rellenar(texto: str, variables: dict) -> str:
    """Reemplaza {variable} por su valor; deja tal cual las que no existen. Recibe texto y variables.
    Es un reemplazo simple (no str.format): una plantilla editada no puede leer atributos internos."""
    return _VARIABLE.sub(lambda m: str(variables.get(m.group(1), m.group(0))), texto or "")


def _variables(evento: str, ctx: dict) -> dict:
    """Valores que pueden usar las plantillas de cada evento. Recibe el evento y su contexto."""
    v = {"enlace_portal": dest.enlace_portal()}
    pedido = ctx.get("pedido")
    if pedido is not None:
        v.update(codigo=_codigo(pedido), nombre=getattr(pedido, "nombre_destinatario", None) or "",
                 secuencia=ctx.get("secuencia", ""), total=ctx.get("total", ""),
                 motivo=(ctx.get("motivo") or "").strip() or "no se pudo contactar al destinatario")
    recojo = ctx.get("recojo")
    if recojo is not None:
        faltantes = [f for f in (ctx.get("faltantes") or []) if f]
        v.update(codigo=getattr(recojo, "codigo", None) or "", cliente=getattr(recojo, "cliente_origen", None) or "cliente",
                 cantidad=getattr(recojo, "cantidad_declarada", None) or 0, n=len(faltantes), faltantes=", ".join(faltantes))
    ruta = ctx.get("ruta")
    if evento == "RETORNOS_ALMACEN" and ruta is not None:
        fallidos = [p for p in (ctx.get("fallidos") or []) if p]
        v.update(codigo_ruta=getattr(ruta, "codigo", None) or "", n=len(fallidos),
                 codigos=", ".join(_codigo(p) for p in fallidos))
    inc = ctx.get("incidencia")
    if inc is not None:
        v.update(codigo=getattr(inc, "codigo", None) or "", placa=getattr(inc, "vehiculo_placa", None) or "sin placa",
                 descripcion=getattr(inc, "descripcion", None) or "sin detalle",
                 conductor=ctx.get("conductor_nombre") or "Conductor en ruta",
                 mecanico=ctx.get("mecanico_nombre") or "un mecánico", telefono=ctx.get("mecanico_telefono") or "")
    reclamo = ctx.get("reclamo")
    if reclamo is not None:
        v.update(codigo=getattr(reclamo, "codigo", None) or "", tipo=getattr(reclamo, "tipo", None) or "RECLAMO",
                 detalle=(getattr(reclamo, "detalle", None) or "").strip())
    if evento == "RESUMEN_DEL_DIA":
        conteos = ctx.get("conteos") or {}
        v.update(fecha=ctx.get("fecha") or "", entregados=conteos.get("entregados", 0),
                 fallidos=conteos.get("fallidos", 0), pendientes=conteos.get("pendientes", 0))
    return v


def _telegram_pedido(ctx: dict, db, evento: str, cuerpo: str, clave: str) -> list[Mensaje]:
    """Arma el aviso de Telegram al destinatario de un pedido."""
    pedido = ctx["pedido"]
    chat_id, nombre_contacto = dest.telegram_contacto(db, "pedido", getattr(pedido, "id", None))
    chat_id = chat_id or (getattr(pedido, "telegram_chat_id", None) or "").strip()
    if not chat_id:
        return []
    return [Mensaje(
        evento=evento,
        canal=Canal.TELEGRAM,
        destinatario=Destinatario("destinatario", chat_id, nombre_contacto or getattr(pedido, "nombre_destinatario", None)),
        cuerpo=cuerpo,
        clave_idempotencia=clave,
        metadatos={"codigo": getattr(pedido, "codigo", None)},
    )]


def _correo(evento: str, tipo: str, email: str, asunto: str, cuerpo: str, clave: str,
            nombre: str | None = None, prioridad: Prioridad = Prioridad.NORMAL) -> Mensaje | None:
    """Arma un correo; vacio si no hay destinatario."""
    if not (email or "").strip():
        return None
    return Mensaje(
        evento=evento,
        canal=Canal.CORREO,
        destinatario=Destinatario(tipo, email.strip(), nombre),
        asunto=asunto,
        cuerpo=cuerpo,
        clave_idempotencia=clave,
        prioridad=prioridad,
    )


def _codigo(pedido) -> str:
    """Codigo del pedido; vacio si no tiene."""
    return getattr(pedido, "codigo", None) or ""


def clave_pedido(evento: str, pedido, ocurrencia: str | None = None) -> str:
    """Clave de idempotencia de un aviso de pedido: evento:codigo[:ocurrencia].
    La ocurrencia (p. ej. R{ruta_id} o H{historial_id}) distingue una nueva vuelta legitima
    del mismo pedido (reprogramado y reasignado); un reintento tecnico conserva la clave."""
    base = f"{evento}:{_codigo(pedido)}"
    return f"{base}:{ocurrencia}" if ocurrencia else base


@registrar("PEDIDO_PROGRAMADO")
def _pedido_programado(ctx: dict, db=None) -> list[Mensaje]:
    """Avisa al destinatario que su pedido fue programado en una ruta."""
    pedido = ctx["pedido"]
    return _telegram_pedido(ctx, db, "PEDIDO_PROGRAMADO",
        f"Hola {getattr(pedido, 'nombre_destinatario', None) or ''}, tu pedido {_codigo(pedido)} "
        f"fue programado para hoy. Sigue su avance en {dest.enlace_portal()}",
        clave_pedido("PEDIDO_PROGRAMADO", pedido, ctx.get("ocurrencia")))


@registrar("PEDIDO_EN_CAMINO")
def _pedido_en_camino(ctx: dict, db=None) -> list[Mensaje]:
    """Avisa al destinatario que su pedido va en camino con su orden de parada."""
    pedido = ctx["pedido"]
    return _telegram_pedido(ctx, db, "PEDIDO_EN_CAMINO",
        f"Tu pedido {_codigo(pedido)} va en camino: eres la parada {ctx['secuencia']} de {ctx['total']}. "
        f"Sigue su avance en {dest.enlace_portal()}",
        clave_pedido("PEDIDO_EN_CAMINO", pedido, ctx.get("ocurrencia")))


@registrar("PEDIDO_ESTA_CERCA")
def _pedido_esta_cerca(ctx: dict, db=None) -> list[Mensaje]:
    """Avisa al destinatario que el repartidor esta por llegar."""
    pedido = ctx["pedido"]
    return _telegram_pedido(ctx, db, "PEDIDO_ESTA_CERCA",
        f"El repartidor esta por llegar a tu direccion con tu pedido {_codigo(pedido)}. "
        f"Sigue su avance en {dest.enlace_portal()}",
        clave_pedido("PEDIDO_ESTA_CERCA", pedido, ctx.get("ocurrencia")))


@registrar("PEDIDO_ENTREGADO")
def _pedido_entregado(ctx: dict, db=None) -> list[Mensaje]:
    """Avisa al destinatario que su pedido fue entregado."""
    pedido = ctx["pedido"]
    return _telegram_pedido(ctx, db, "PEDIDO_ENTREGADO",
        f"Hola {getattr(pedido, 'nombre_destinatario', None) or ''}, tu pedido {_codigo(pedido)} fue entregado con éxito. "
        f"Verifica el comprobante en {dest.enlace_portal()}",
        clave_pedido("PEDIDO_ENTREGADO", pedido, ctx.get("ocurrencia")))


@registrar("PEDIDO_NO_ENTREGADO")
def _pedido_no_entregado(ctx: dict, db=None) -> list[Mensaje]:
    """Avisa al destinatario que no se pudo entregar su pedido y el motivo."""
    pedido = ctx["pedido"]
    motivo = (ctx.get("motivo") or "").strip() or "no se pudo contactar al destinatario"
    return _telegram_pedido(ctx, db, "PEDIDO_NO_ENTREGADO",
        f"No pudimos entregar tu pedido {_codigo(pedido)}: {motivo}. "
        f"Lo reprogramaremos; sigue su avance en {dest.enlace_portal()}",
        clave_pedido("PEDIDO_NO_ENTREGADO", pedido, ctx.get("ocurrencia")))


@registrar("PEDIDO_REPROGRAMADO")
def _pedido_reprogramado(ctx: dict, db=None) -> list[Mensaje]:
    """Avisa al destinatario que su pedido fallido se reprogramo."""
    pedido = ctx["pedido"]
    return _telegram_pedido(ctx, db, "PEDIDO_REPROGRAMADO",
        f"Tu pedido {_codigo(pedido)} fue reprogramado y saldra en una nueva ruta. "
        f"Sigue su avance en {dest.enlace_portal()}",
        clave_pedido("PEDIDO_REPROGRAMADO", pedido, ctx.get("ocurrencia")))


@registrar("RECOJO_COMPLETADO")
def _recojo_completado(ctx: dict, db=None) -> list[Mensaje]:
    """Avisa al cliente y al almacen que el recojo se completo."""
    recojo = ctx["recojo"]
    cliente = ctx.get("cliente")
    codigo = getattr(recojo, "codigo", None) or ""
    cantidad = getattr(recojo, "cantidad_declarada", None) or 0
    nombre_cliente = getattr(recojo, "cliente_origen", None) or "cliente"
    mensajes = [
        _correo("RECOJO_COMPLETADO", "cliente_corporativo", dest.email_cliente(cliente) if cliente else "",
                f"Recojo {codigo} completado",
                f"El recojo {codigo} de {nombre_cliente} fue completado con {cantidad} bultos.",
                f"RECOJO_COMPLETADO:{codigo}:cliente", nombre_cliente),
        _correo("RECOJO_COMPLETADO", "almacen", dest.email_almacen(),
                f"Recojo {codigo} completado",
                f"El recojo {codigo} de {nombre_cliente} fue completado con {cantidad} bultos. "
                f"Ingresa a Almacen para su recepcion.",
                f"RECOJO_COMPLETADO:{codigo}:almacen"),
    ]
    return [m for m in mensajes if m]


@registrar("PAQUETES_FALTANTES")
def _paquetes_faltantes(ctx: dict, db=None) -> list[Mensaje]:
    """Avisa al cliente y al administrador que hubo paquetes faltantes en el ingreso."""
    recojo = ctx["recojo"]
    cliente = ctx.get("cliente")
    faltantes = [f for f in (ctx.get("faltantes") or []) if f]
    if not faltantes:
        return []
    codigo = getattr(recojo, "codigo", None) or ""
    nombre_cliente = getattr(recojo, "cliente_origen", None) or "cliente"
    detalle = ", ".join(faltantes)
    mensajes = [
        _correo("PAQUETES_FALTANTES", "cliente_corporativo", dest.email_cliente(cliente) if cliente else "",
                f"Paquetes faltantes en {codigo}",
                f"En el ingreso del recojo {codigo} faltaron {len(faltantes)} paquete(s): {detalle}.",
                f"PAQUETES_FALTANTES:{codigo}:cliente", nombre_cliente),
        _correo("PAQUETES_FALTANTES", "administrador", dest.email_admin(),
                f"Paquetes faltantes en {codigo}",
                f"El recojo {codigo} de {nombre_cliente} tuvo {len(faltantes)} paquete(s) faltante(s): {detalle}.",
                f"PAQUETES_FALTANTES:{codigo}:admin"),
    ]
    return [m for m in mensajes if m]


@registrar("RETORNOS_ALMACEN")
def _retornos_almacen(ctx: dict, db=None) -> list[Mensaje]:
    """Avisa al almacen que la ruta dejo pedidos fallidos para retorno."""
    ruta = ctx["ruta"]
    fallidos = [p for p in (ctx.get("fallidos") or []) if p]
    if not fallidos:
        return []
    codigo_ruta = getattr(ruta, "codigo", None) or ""
    codigos = ", ".join(_codigo(p) for p in fallidos)
    mensaje = _correo("RETORNOS_ALMACEN", "almacen", dest.email_almacen(),
                       f"Retornos al almacen — ruta {codigo_ruta}",
                       f"La ruta {codigo_ruta} termino con {len(fallidos)} pedido(s) fallido(s): {codigos}.",
                       f"RETORNOS_ALMACEN:{codigo_ruta}")
    return [mensaje] if mensaje else []


@registrar("AUXILIO_MECANICO")
def _auxilio_mecanico(ctx: dict, db=None) -> list[Mensaje]:
    """Aviso urgente al administrador (WhatsApp y correo) cuando un conductor reporta averia."""
    inc = ctx["incidencia"]
    ruta = ctx.get("ruta")
    codigo = getattr(inc, "codigo", None) or ""
    descripcion = (getattr(inc, "descripcion", None) or "sin detalle")
    placa = getattr(inc, "vehiculo_placa", None) or "sin placa"
    nombre_ruta = getattr(ruta, "nombre", None) or getattr(ruta, "codigo", None) or "su ruta"
    cuerpo = (f"AUXILIO MECANICO — {codigo}\nVehiculo: {placa}\n"
              f"Ruta: {nombre_ruta}\nFalla: {descripcion}")
    mensajes = []
    chat_id = dest.telegram_admin()
    if chat_id:
        mensajes.append(Mensaje(
            evento="AUXILIO_MECANICO", canal=Canal.TELEGRAM,
            destinatario=Destinatario("administrador", chat_id),
            cuerpo=cuerpo, clave_idempotencia=f"AUXILIO_MECANICO:{codigo}:telegram",
            prioridad=Prioridad.URGENTE,
        ))
    correo = _correo("AUXILIO_MECANICO", "administrador", dest.email_admin(),
                     f"Auxilio mecanico {codigo}", cuerpo, f"AUXILIO_MECANICO:{codigo}:correo",
                     prioridad=Prioridad.URGENTE)
    if correo:
        mensajes.append(correo)
    return mensajes


@registrar("AYUDA_ASIGNADA")
def _ayuda_asignada(ctx: dict, db=None) -> list[Mensaje]:
    """Avisa al mecanico que se le asigno un auxilio.
    Incluye placa, falla, nombre y telefono del conductor y mapa de la averia."""
    inc = ctx["incidencia"]
    chat_id = (ctx.get("mecanico_chat_id") or "").strip()
    if not chat_id:
        chat_id, _ = dest.telegram_contacto(db, "mecanico", ctx.get("mecanico_id"))
    if not chat_id:
        return []

    codigo = getattr(inc, "codigo", None) or ""
    placa = getattr(inc, "vehiculo_placa", None) or "sin placa"
    descripcion = (getattr(inc, "descripcion", None) or "sin detalle")
    conductor = ctx.get("conductor_nombre") or "Conductor en ruta"
    telefono_cond = ctx.get("conductor_telefono") or ""
    contacto_conductor = f"{conductor} ({telefono_cond})" if telefono_cond else conductor

    mapa = ""
    lat, lon = getattr(inc, "latitud", None), getattr(inc, "longitud", None)
    if lat is not None and lon is not None:
        mapa = f"\nUbicación avería: https://maps.google.com/?q={lat},{lon}"

    cuerpo = (
        f"🚨 AUXILIO ASIGNADO — {codigo}\n"
        f"Vehículo: {placa}\n"
        f"Falla: {descripcion}\n"
        f"Conductor: {contacto_conductor}"
        f"{mapa}\n\n"
        f"Responde con 'VOY' para confirmar o 'NO PUEDO' para reasignar."
    )

    return [Mensaje(
        evento="AYUDA_ASIGNADA", canal=Canal.TELEGRAM,
        destinatario=Destinatario("mecanico", chat_id, ctx.get("mecanico_nombre")),
        cuerpo=cuerpo,
        clave_idempotencia=f"AYUDA_ASIGNADA:{codigo}:{ctx.get('mecanico_id', 0)}",
        prioridad=Prioridad.URGENTE,
    )]


@registrar("AYUDA_EN_CAMINO")
def _ayuda_en_camino(ctx: dict, db=None) -> list[Mensaje]:
    """Avisa al conductor que el mecanico va en camino."""
    inc = ctx["incidencia"]
    chat_id = (ctx.get("conductor_chat_id") or "").strip()
    if not chat_id:
        chat_id, _ = dest.telegram_contacto(db, "conductor", ctx.get("conductor_id"))
    if not chat_id:
        return []
    codigo = getattr(inc, "codigo", None) or ""
    mecanico = ctx.get("mecanico_nombre") or "un mecanico"
    taller = ctx.get("mecanico_taller") or ""
    telefono_mecanico = ctx.get("mecanico_telefono") or ""
    return [Mensaje(
        evento="AYUDA_EN_CAMINO", canal=Canal.TELEGRAM,
        destinatario=Destinatario("conductor", chat_id),
        cuerpo=(f"Tu auxilio {codigo} va en camino: {mecanico}"
                + (f" ({taller})" if taller else "")
                + (f", telefono {telefono_mecanico}" if telefono_mecanico else "") + "."),
        clave_idempotencia=f"AYUDA_EN_CAMINO:{codigo}",
    )]


@registrar("RECLAMO_NUEVO")
def _reclamo_nuevo(ctx: dict, db=None) -> list[Mensaje]:
    """Avisa al administrador que se registro un reclamo en el Libro de Reclamaciones."""
    reclamo = ctx["reclamo"]
    codigo = getattr(reclamo, "codigo", None) or ""
    tipo = getattr(reclamo, "tipo", None) or "RECLAMO"
    detalle = (getattr(reclamo, "detalle", None) or "").strip()
    pedido = getattr(reclamo, "pedido_codigo", None) or "sin pedido"
    correo = _correo("RECLAMO_NUEVO", "administrador", dest.email_admin(),
                     f"Nuevo {tipo.lower()} {codigo}",
                     f"Codigo: {codigo}\nTipo: {tipo}\nPedido: {pedido}\nDetalle: {detalle}",
                     f"RECLAMO_NUEVO:{codigo}")
    return [correo] if correo else []


@registrar("RESUMEN_DEL_DIA")
def _resumen_del_dia(ctx: dict, db=None) -> list[Mensaje]:
    """Resumen diario de la operacion para el cliente corporativo."""
    cliente = ctx["cliente"]
    conteos = ctx.get("conteos") or {}
    fecha = ctx.get("fecha") or ""
    nombre = getattr(cliente, "razon_social", None) or "cliente"
    correo = _correo("RESUMEN_DEL_DIA", "cliente_corporativo", dest.email_cliente(cliente),
                     f"Resumen del dia {fecha} — {nombre}",
                     (f"Entregados: {conteos.get('entregados', 0)}\n"
                      f"Fallidos: {conteos.get('fallidos', 0)}\n"
                      f"Pendientes: {conteos.get('pendientes', 0)}"),
                     f"RESUMEN_DEL_DIA:{getattr(cliente, 'id', None)}:{fecha}", nombre)
    return [correo] if correo else []
