# app/services/pedido_service.py
# La inteligencia del módulo Inbound.
import io
from datetime import datetime
import pandas as pd
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.pedido import Pedido
from app.models.conductor import PerfilConductor
from app.repositories import (
    pedido_repository, cliente_repository, historial_repository, ruta_repository, usuario_repository,
    reporte_repository,
)
from app.services.geocoder import obtener_coordenadas
from app.core.codigos import asignar_codigo, generar_codigo, PREFIJO_PEDIDO

# Columna mínima obligatoria del Excel (el nombre del cliente se valida aparte).
COLUMNAS_REQUERIDAS = ["direccion_destino"]


def _valor(fila, df, *nombres):
    """Devuelve el primer valor no vacío entre varias columnas posibles del Excel."""
    for n in nombres:
        if n in df.columns and pd.notna(fila.get(n)):
            return fila[n]
    return None


def parsear_filas_excel(contenido: bytes, nombre_archivo: str) -> list[dict]:
    """Solo lectura y normalización del Excel; sin base de datos ni matcheo de cliente.
    Recibe: bytes del archivo y su nombre. Devuelve lista de dicts con las claves
    estandarizadas por fila (incluyendo razon_social_cliente para que el llamador la
    resuelva si lo necesita)."""
    # Validar extensión antes de intentar leer.
    if not nombre_archivo.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="El archivo debe ser un Excel (.xlsx)")

    try:
        df = pd.read_excel(io.BytesIO(contenido))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error leyendo el archivo: {e}")

    # Columna de destino obligatoria.
    if not all(col in df.columns for col in COLUMNAS_REQUERIDAS):
        raise HTTPException(status_code=400, detail=f"El Excel debe contener: {COLUMNAS_REQUERIDAS}")
    if "razon_social_cliente" not in df.columns and "cliente_origen" not in df.columns:
        raise HTTPException(
            status_code=400,
            detail="El Excel debe incluir 'razon_social_cliente' (o 'cliente_origen').",
        )

    filas: list[dict] = []
    for _, fila in df.iterrows():
        referencia = _str_o_none(_valor(fila, df, "referencia_externa", "numero_tracking", "id"))
        peso = _valor(fila, df, "peso_kg")
        volumen = _valor(fila, df, "volumen_m3")
        filas.append({
            "referencia_externa": referencia,
            "razon_social_cliente": str(_valor(fila, df, "razon_social_cliente", "cliente_origen") or "").strip(),
            "direccion_destino": str(fila["direccion_destino"]),
            "nombre_destinatario": _str_o_none(_valor(fila, df, "nombre_destinatario")),
            "telefono_destinatario": _str_o_none(_valor(fila, df, "telefono_destinatario")),
            "dni_destinatario": _str_o_none(_valor(fila, df, "dni_destinatario")),
            "peso_kg": float(peso) if peso is not None else 0.0,
            "volumen_m3": float(volumen) if volumen is not None else 0.0,
        })
    return filas


def crear_pedido_desde_fila(
    db: Session,
    fila: dict,
    cliente,
    recojo_id: int | None,
    estado: str,
    usuario_id: int | None,
    geocodificar: bool = True,
) -> Pedido:
    """Construye y persiste un Pedido con el cliente ya resuelto por el llamador.
    Recibe: sesión DB, fila normalizada, objeto cliente, id de recojo origen (o None),
    estado inicial, el id del usuario que ejecuta la acción y si geocodificar en línea.
    Si geocodificar=True intenta el destino al vuelo (si falla conserva el estado, lat/lng
    quedan en None). Si geocodificar=False deja lat/lng en None para resolverlos después
    (p.ej. en segundo plano al aceptar un recojo masivo, para no bloquear la petición)."""
    pedido = Pedido(
        referencia_externa=fila["referencia_externa"],
        cliente_id=cliente.id,
        cliente_origen=cliente.razon_social,  # snapshot del nombre real registrado
        direccion_destino=fila["direccion_destino"],
        nombre_destinatario=fila.get("nombre_destinatario"),
        telefono_destinatario=fila.get("telefono_destinatario"),
        dni_destinatario=fila.get("dni_destinatario"),
        peso_kg=fila.get("peso_kg", 0.0),
        volumen_m3=fila.get("volumen_m3", 0.0),
        recojo_id=recojo_id,
        estado=estado,
    )
    db.add(pedido)
    db.flush()  # obtener id antes del geocoder
    asignar_codigo(db, pedido, PREFIJO_PEDIDO)
    historial_repository.registrar(db, pedido.id, None, estado, usuario_id)

    # Geocodificación inmediata; si falla se conserva el estado recibido (no GEOCODIFICACION_FALLIDA)
    # para no perder el estado semántico del pedido (p.ej. POR_RECOGER).
    if geocodificar:
        lat, lng = obtener_coordenadas(pedido.direccion_destino)
        if lat and lng:
            pedido.latitud = lat
            pedido.longitud = lng
            partes = pedido.direccion_destino.split(",")
            pedido.distrito = partes[1].strip() if len(partes) >= 2 else "ZONA_DESCONOCIDA"

    return pedido


def crear_pedidos_bulk(
    db: Session,
    filas: list[dict],
    cliente,
    recojo_id: int | None,
    estado: str,
    usuario_id: int | None,
) -> list[Pedido]:
    """Crea MUCHOS pedidos del mismo recojo en bloque, SIN geocodificar y con el mínimo de
    idas y vueltas a la BD: un flush para todos los pedidos (asigna ids+códigos) y un
    registrar_bulk para todo el historial. Reemplaza al bucle que hacía ~2 flush por fila
    (~400 round-trips para 200 filas sobre Supabase). NO hace commit: lo hace el llamador.
    Recibe: filas ya validadas, el cliente resuelto, el recojo origen, el estado inicial y el usuario."""
    pedidos = [
        Pedido(
            referencia_externa=fila["referencia_externa"],
            cliente_id=cliente.id,
            cliente_origen=cliente.razon_social,
            direccion_destino=fila["direccion_destino"],
            nombre_destinatario=fila.get("nombre_destinatario"),
            telefono_destinatario=fila.get("telefono_destinatario"),
            dni_destinatario=fila.get("dni_destinatario"),
            peso_kg=fila.get("peso_kg", 0.0),
            volumen_m3=fila.get("volumen_m3", 0.0),
            recojo_id=recojo_id,
            estado=estado,
        )
        for fila in filas
    ]
    db.add_all(pedidos)
    db.flush()  # un solo flush para todos los ids
    for pedido in pedidos:
        pedido.codigo = generar_codigo(PREFIJO_PEDIDO, pedido.id)
    historial_repository.registrar_bulk(
        db,
        [{"pedido_id": p.id, "estado_anterior": None, "estado_nuevo": estado, "usuario_id": usuario_id} for p in pedidos],
    )
    return pedidos


def cargar_pedidos_excel(db: Session, contenido: bytes, nombre_archivo: str, usuario_id: int | None = None) -> dict:
    """
    CUS-13: crea los pedidos nuevos a partir del Excel.
    Usa los helpers parsear_filas_excel y crear_pedido_desde_fila; mantiene el
    comportamiento histórico (rechazo de filas sin cliente, dedup por referencia_externa,
    estado LISTO_PARA_ENVIO, sin recojo asociado).
    """
    filas = parsear_filas_excel(contenido, nombre_archivo)

    nuevos: list[Pedido] = []
    rechazados: list[dict] = []
    for i, fila in enumerate(filas):
        fila_num = i + 2  # fila del Excel (1 = encabezado)
        referencia = fila["referencia_externa"]
        if referencia and pedido_repository.obtener_por_referencia_externa(db, referencia):
            continue  # ya se importó antes -> no duplicar

        # Cliente (empresa que envía): DEBE existir; si no, se rechaza la fila.
        cliente = cliente_repository.buscar_por_razon_social_normalizada(db, fila["razon_social_cliente"])
        if cliente is None:
            rechazados.append({
                "fila": fila_num,
                "cliente": fila["razon_social_cliente"] or "(vacío)",
                "motivo": "Cliente no registrado",
            })
            continue

        pedido = crear_pedido_desde_fila(db, fila, cliente, recojo_id=None, estado="LISTO_PARA_ENVIO", usuario_id=usuario_id)
        nuevos.append(pedido)

    if nuevos:
        db.commit()

    # Geocodificar los que quedaron sin coordenadas (fallo en crear_pedido_desde_fila).
    geo = procesar_geocodificacion(db, usuario_id) if nuevos else {}

    return {
        "mensaje": "Carga masiva exitosa",
        "pedidos_nuevos": len(nuevos),
        "total_filas_leidas": len(filas),
        "pedidos_geocodificados": geo.get("pedidos_exitosos", 0),
        "pedidos_fallidos": geo.get("pedidos_fallidos", 0),
        "rechazados": rechazados,
        "total_rechazados": len(rechazados),
    }


def _str_o_none(valor):
    """Convierte a texto, o deja None si el valor es nulo."""
    return str(valor) if valor is not None else None


def procesar_geocodificacion(db: Session, usuario_id: int | None = None) -> dict:
    """
    CUS-15: geocodifica los pedidos sin coordenadas. Si una dirección no se
    encuentra, marca el pedido como fallido y lo registra en el historial.
    """
    pendientes = pedido_repository.obtener_sin_coordenadas(db)
    if not pendientes:
        return {"mensaje": "Todos los pedidos ya están geocodificados"}

    exitosos = 0
    fallidos = 0

    for pedido in pendientes:
        lat, lng = obtener_coordenadas(pedido.direccion_destino)

        if lat and lng:
            pedido.latitud = lat
            pedido.longitud = lng
            partes = pedido.direccion_destino.split(",")
            pedido.distrito = partes[1].strip() if len(partes) >= 2 else "ZONA_DESCONOCIDA"
            exitosos += 1
        elif pedido.estado != "POR_RECOGER":
            # Defensa en profundidad: nunca pisar el estado de un POR_RECOGER. El filtro de
            # obtener_sin_coordenadas ya los excluye, pero si por algún flujo llegara uno aquí,
            # se conserva su estado (esos se geocodifican al aceptar/validar, no en este lote).
            estado_anterior = pedido.estado
            pedido.estado = "GEOCODIFICACION_FALLIDA"
            historial_repository.registrar(db, pedido.id, estado_anterior, "GEOCODIFICACION_FALLIDA", usuario_id)
            fallidos += 1

    pedido_repository.guardar_cambios(db)

    return {
        "mensaje": "Proceso de geocodificación finalizado",
        "pedidos_exitosos": exitosos,
        "pedidos_fallidos": fallidos,
    }


def _nombres_conductores(db: Session, ids: set[int]) -> dict:
    """{usuario_id: nombre (o correo si no tiene perfil)} para un conjunto de conductores."""
    if not ids:
        return {}
    nombres = {
        p.usuario_id: p.nombre
        for p in db.query(PerfilConductor).filter(PerfilConductor.usuario_id.in_(ids)).all()
    }
    for cid in ids:
        if not nombres.get(cid):
            u = usuario_repository.obtener_por_id(db, cid)
            nombres[cid] = u.correo if u else None
    return nombres


def listar_pedidos(db: Session, skip: int, limit: int):
    """Devuelve los pedidos paginados, enriquecidos con su ruta y conductor asignados."""
    pedidos = pedido_repository.listar(db, skip=skip, limit=limit)
    mapa = ruta_repository.mapa_ruta_por_pedidos(db, [p.id for p in pedidos])
    nombres = _nombres_conductores(db, {cid for (_, cid) in mapa.values() if cid})
    for p in pedidos:
        ruta_nombre, conductor_id = mapa.get(p.id, (None, None))
        # Atributos extra que lee PedidoResponse (no se guardan en la BD).
        p.ruta_nombre = ruta_nombre
        p.conductor_nombre = nombres.get(conductor_id)
    return pedidos


def reabrir_pedido(db: Session, pedido_id: int, usuario_id: int | None = None) -> dict:
    """Devuelve un pedido FALLIDO al estado LISTO_PARA_ENVIO y lo saca de su ruta para
    poder reasignarlo. Recibe: pedido_id (int) y el id del admin."""
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    estado_anterior = pedido.estado
    ruta_repository.eliminar_detalles_de_pedido(db, pedido_id)
    pedido.estado = "LISTO_PARA_ENVIO"
    pedido.fecha_entrega = None
    historial_repository.registrar(db, pedido.id, estado_anterior, "LISTO_PARA_ENVIO", usuario_id)
    db.commit()
    return {"mensaje": "Pedido reabierto. Ya puedes reasignarlo.", "codigo": pedido.codigo}


def _exigir_fallido(pedido) -> None:
    """Valida que el pedido esté en FALLIDO antes de decidir su devolución."""
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    if pedido.estado != "FALLIDO":
        raise HTTPException(status_code=400, detail="Solo se pueden decidir pedidos en estado FALLIDO")


def reprogramar(db: Session, pedido_id: int, usuario_id: int | None = None) -> dict:
    """CUS-31: el admin decide reintentar el pedido mañana: vuelve a LISTO_PARA_ENVIO y sale
    de su ruta para reasignarlo. Recibe: pedido_id y el id del admin."""
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    _exigir_fallido(pedido)
    estado_anterior = pedido.estado
    ruta_repository.eliminar_detalles_de_pedido(db, pedido_id)
    pedido.estado = "LISTO_PARA_ENVIO"
    pedido.fecha_entrega = None
    historial_repository.registrar(db, pedido.id, estado_anterior, "LISTO_PARA_ENVIO", usuario_id)
    db.commit()
    reporte_repository.cerrar_abierto_de_pedido(db, pedido_id, "Reprogramado", usuario_id)
    return {"mensaje": "Pedido reprogramado. Volvió a su zona para reasignarlo.", "codigo": pedido.codigo}


def cancelar(db: Session, pedido_id: int, usuario_id: int | None = None) -> dict:
    """CUS-31: el admin decide cancelar el pedido (estado terminal CANCELADO). Recibe:
    pedido_id y el id del admin."""
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    _exigir_fallido(pedido)
    estado_anterior = pedido.estado
    # Desvincula el detalle de ruta para que el estado efectivo caiga en pedido.estado = CANCELADO
    # (mismo patrón que reprogramar, evita que siga apareciendo como FALLIDO en seguimiento).
    ruta_repository.eliminar_detalles_de_pedido(db, pedido_id)
    pedido.estado = "CANCELADO"
    pedido.fecha_entrega = None
    historial_repository.registrar(db, pedido.id, estado_anterior, "CANCELADO", usuario_id)
    db.commit()
    reporte_repository.cerrar_abierto_de_pedido(db, pedido_id, "Cancelado", usuario_id)
    return {"mensaje": "Pedido cancelado.", "codigo": pedido.codigo}


def agrupar_por_zona(db: Session) -> dict:
    """CUS-16: arma la lista de zonas operativas con su conteo de pedidos."""
    resultados = pedido_repository.agrupar_por_zona(db)
    zonas = [{"distrito": r.distrito, "total_pedidos": r.total_pedidos} for r in resultados]
    return {"zonas_operativas": zonas}


# --- CUS-17: resolución manual de direcciones ---
def listar_para_ubicar(db: Session):
    """Pedidos sin coordenadas en cualquier estado resoluble por el admin (LISTO_PARA_ENVIO,
    POR_RECOGER o GEOCODIFICACION_FALLIDA), para ubicarlos a mano en el mapa."""
    return pedido_repository.listar_sin_ubicacion_resoluble(db)


def buscar_direccion(direccion: str) -> dict:
    """CUS-17: geocodifica un texto de búsqueda (dirección/lugar) usando Nominatim,
    para ayudar al admin a ubicar el pin en el mapa. Recibe: el texto. Devuelve:
    {encontrado, latitud, longitud}."""
    lat, lng = obtener_coordenadas((direccion or "").strip())
    if lat is None or lng is None:
        return {"encontrado": False, "latitud": None, "longitud": None}
    return {"encontrado": True, "latitud": lat, "longitud": lng}


def fijar_ubicacion(db: Session, pedido_id: int, latitud: float, longitud: float,
                    direccion: str | None = None, usuario_id: int | None = None) -> dict:
    """CUS-17: fija a mano las coordenadas de un pedido (y opcionalmente corrige su
    dirección). Si estaba en GEOCODIFICACION_FALLIDA, vuelve a LISTO_PARA_ENVIO para poder
    rutearlo. Recibe: id, lat/lng, dirección opcional y el id del admin."""
    pedido = pedido_repository.obtener_por_id(db, pedido_id)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    pedido.latitud = latitud
    pedido.longitud = longitud
    if direccion and direccion.strip():
        pedido.direccion_destino = direccion.strip()
    # Deducimos el distrito del texto de la dirección (igual que en la geocodificación):
    # si no hay coma, queda 'ZONA_DESCONOCIDA' para que igual sea agrupable/ruteable.
    partes = (pedido.direccion_destino or "").split(",")
    pedido.distrito = partes[1].strip() if len(partes) >= 2 else "ZONA_DESCONOCIDA"

    # Transición de estado según el estado actual:
    # - GEOCODIFICACION_FALLIDA: ya quedó resuelta, pasa a LISTO_PARA_ENVIO para rutearlo.
    # - POR_RECOGER: se fijaron las coordenadas pero conserva su estado semántico.
    # - Cualquier otro estado: solo se actualizan las coordenadas, sin cambiar estado.
    if pedido.estado == "GEOCODIFICACION_FALLIDA":
        historial_repository.registrar(db, pedido.id, pedido.estado, "LISTO_PARA_ENVIO", usuario_id)
        pedido.estado = "LISTO_PARA_ENVIO"

    db.commit()
    return {"mensaje": "Ubicación actualizada", "codigo": pedido.codigo}


def resolver_observado(db: Session, pedido_id: int, usuario_id: int | None = None) -> dict:
    """Resuelve un pedido OBSERVADO (faltante/discrepancia ya aclarada): lo pasa a
    LISTO_PARA_ENVIO. Recibe: pedido_id y el id del usuario (almacén/admin)."""
    pedido = pedido_repository.obtener_por_id(db, pedido_id)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    if pedido.estado != "OBSERVADO":
        raise HTTPException(status_code=400, detail="Solo se puede resolver un pedido en estado OBSERVADO")
    historial_repository.registrar(db, pedido.id, "OBSERVADO", "LISTO_PARA_ENVIO", usuario_id)
    pedido.estado = "LISTO_PARA_ENVIO"
    pedido.validado_en = datetime.utcnow()
    pedido.validado_por = usuario_id
    db.commit()
    return {"mensaje": "Pedido resuelto: Listo para envío.", "codigo": pedido.codigo}


def regeocodificar_pedidos() -> None:
    """Tarea en segundo plano: re-geocodifica los pedidos NO terminales para refrescar sus
    coordenadas. Útil tras activar Google Geocoding (corrige los puntos apilados que dejó
    Nominatim). Abre su PROPIA sesión de BD; hace commit por pedido para ir actualizando el mapa.
    No recibe parámetros (la usa un BackgroundTask)."""
    from app.db.database import SessionLocal

    estados = ("POR_RECOGER", "OBSERVADO", "LISTO_PARA_ENVIO", "ASIGNADO", "EN_RUTA", "GEOCODIFICACION_FALLIDA")
    db = SessionLocal()
    try:
        pedidos = db.query(Pedido).filter(Pedido.estado.in_(estados)).all()
        for pedido in pedidos:
            lat, lng = obtener_coordenadas(pedido.direccion_destino)
            if lat and lng:
                pedido.latitud = lat
                pedido.longitud = lng
                partes = (pedido.direccion_destino or "").split(",")
                pedido.distrito = partes[1].strip() if len(partes) >= 2 else "ZONA_DESCONOCIDA"
                db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
