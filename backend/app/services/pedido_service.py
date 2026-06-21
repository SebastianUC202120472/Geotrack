# app/services/pedido_service.py
# La inteligencia del módulo Inbound.
import io
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
from app.core.codigos import asignar_codigo, PREFIJO_PEDIDO

# Columna mínima obligatoria del Excel (el nombre del cliente se valida aparte).
COLUMNAS_REQUERIDAS = ["direccion_destino"]


def _valor(fila, df, *nombres):
    """Devuelve el primer valor no vacío entre varias columnas posibles del Excel."""
    for n in nombres:
        if n in df.columns and pd.notna(fila.get(n)):
            return fila[n]
    return None


def cargar_pedidos_excel(db: Session, contenido: bytes, nombre_archivo: str, usuario_id: int | None = None) -> dict:
    """
    CUS-13: crea los pedidos nuevos a partir del Excel.
    Por cada fila: crea/enlaza el cliente, guarda destinatario y deja el primer
    evento de trazabilidad (REGISTRADO).
    """
    # 1) Validación de formato (antes del try -> devuelve un 400 limpio).
    if not nombre_archivo.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="El archivo debe ser un Excel (.xlsx)")

    # 2) Leer el Excel.
    try:
        df = pd.read_excel(io.BytesIO(contenido))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error leyendo el archivo: {e}")

    # 3) Validar columnas obligatorias + que exista alguna columna con el cliente.
    if not all(col in df.columns for col in COLUMNAS_REQUERIDAS):
        raise HTTPException(status_code=400, detail=f"El Excel debe contener: {COLUMNAS_REQUERIDAS}")
    if "razon_social_cliente" not in df.columns and "cliente_origen" not in df.columns:
        raise HTTPException(
            status_code=400,
            detail="El Excel debe incluir 'razon_social_cliente' (o 'cliente_origen').",
        )

    # 4) Construir los pedidos nuevos. El cliente DEBE estar registrado (ya no se crea).
    nuevos: list[Pedido] = []
    rechazados: list[dict] = []
    for i, (_, fila) in enumerate(df.iterrows()):
        fila_num = i + 2  # fila del Excel (1 = encabezado)
        referencia = _str_o_none(_valor(fila, df, "referencia_externa", "numero_tracking", "id"))
        if referencia and pedido_repository.obtener_por_referencia_externa(db, referencia):
            continue  # ya se importó antes -> no duplicar

        # Cliente (empresa que envía): DEBE existir; si no, se rechaza la fila.
        razon = str(_valor(fila, df, "razon_social_cliente", "cliente_origen") or "").strip()
        cliente = cliente_repository.buscar_por_razon_social_normalizada(db, razon)
        if cliente is None:
            rechazados.append({"fila": fila_num, "cliente": razon or "(vacío)", "motivo": "Cliente no registrado"})
            continue

        peso = _valor(fila, df, "peso_kg")
        volumen = _valor(fila, df, "volumen_m3")
        nuevos.append(
            Pedido(
                referencia_externa=referencia,
                cliente_id=cliente.id,
                cliente_origen=cliente.razon_social,  # snapshot del nombre real registrado
                direccion_destino=str(fila["direccion_destino"]),
                nombre_destinatario=_str_o_none(_valor(fila, df, "nombre_destinatario")),
                telefono_destinatario=_str_o_none(_valor(fila, df, "telefono_destinatario")),
                dni_destinatario=_str_o_none(_valor(fila, df, "dni_destinatario")),
                peso_kg=float(peso) if peso is not None else 0.0,
                volumen_m3=float(volumen) if volumen is not None else 0.0,
            )
        )

    # 5) Guardar pedidos: asignar el código PD-001 y registrar el evento inicial.
    if nuevos:
        db.add_all(nuevos)
        db.flush()  # asigna ids sin cerrar la transacción
        for p in nuevos:
            asignar_codigo(db, p, PREFIJO_PEDIDO)  # codigo legible PD-001 (= tracking/QR)
            historial_repository.registrar(db, p.id, None, "PENDIENTE", usuario_id)
        db.commit()

    # 6) Geocodificar de inmediato (CUS-15). Se hace por dentro, en la misma
    #    carga, para que el admin no tenga que lanzar un paso manual aparte:
    #    apenas sube el Excel, los pedidos ya quedan con coordenadas y distrito.
    geo = procesar_geocodificacion(db, usuario_id) if nuevos else {}

    return {
        "mensaje": "Carga masiva exitosa",
        "pedidos_nuevos": len(nuevos),
        "total_filas_leidas": len(df),
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
        else:
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
    """Devuelve un pedido FALLIDO al estado PENDIENTE y lo saca de su ruta para
    poder reasignarlo. Recibe: pedido_id (int) y el id del admin."""
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    estado_anterior = pedido.estado
    ruta_repository.eliminar_detalles_de_pedido(db, pedido_id)
    pedido.estado = "PENDIENTE"
    pedido.fecha_entrega = None
    historial_repository.registrar(db, pedido.id, estado_anterior, "PENDIENTE", usuario_id)
    db.commit()
    return {"mensaje": "Pedido reabierto. Ya puedes reasignarlo.", "codigo": pedido.codigo}


def _exigir_fallido(pedido) -> None:
    """Valida que el pedido esté en FALLIDO antes de decidir su devolución."""
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    if pedido.estado != "FALLIDO":
        raise HTTPException(status_code=400, detail="Solo se pueden decidir pedidos en estado FALLIDO")


def reprogramar(db: Session, pedido_id: int, usuario_id: int | None = None) -> dict:
    """CUS-31: el admin decide reintentar el pedido mañana: vuelve a PENDIENTE y sale de
    su ruta para reasignarlo. Recibe: pedido_id y el id del admin."""
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    _exigir_fallido(pedido)
    estado_anterior = pedido.estado
    ruta_repository.eliminar_detalles_de_pedido(db, pedido_id)
    pedido.estado = "PENDIENTE"
    pedido.fecha_entrega = None
    historial_repository.registrar(db, pedido.id, estado_anterior, "PENDIENTE", usuario_id)
    db.commit()
    reporte_repository.cerrar_abierto_de_pedido(db, pedido_id, "Reprogramado")
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
    reporte_repository.cerrar_abierto_de_pedido(db, pedido_id, "Cancelado")
    return {"mensaje": "Pedido cancelado.", "codigo": pedido.codigo}


def agrupar_por_zona(db: Session) -> dict:
    """CUS-16: arma la lista de zonas operativas con su conteo de pedidos."""
    resultados = pedido_repository.agrupar_por_zona(db)
    zonas = [{"distrito": r.distrito, "total_pedidos": r.total_pedidos} for r in resultados]
    return {"zonas_operativas": zonas}


# --- CUS-17: resolución manual de direcciones ---
def listar_para_ubicar(db: Session):
    """CUS-17: pedidos con la geocodificación fallida, para resolverlos a mano."""
    return pedido_repository.listar_geocodificacion_fallida(db)


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
    dirección). Si estaba en GEOCODIFICACION_FALLIDA, vuelve a PENDIENTE para poder
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

    # Si la dirección estaba fallida, ya quedó resuelta: vuelve a la cola (PENDIENTE).
    if pedido.estado == "GEOCODIFICACION_FALLIDA":
        historial_repository.registrar(db, pedido.id, pedido.estado, "PENDIENTE", usuario_id)
        pedido.estado = "PENDIENTE"

    db.commit()
    return {"mensaje": "Ubicación actualizada", "codigo": pedido.codigo}
