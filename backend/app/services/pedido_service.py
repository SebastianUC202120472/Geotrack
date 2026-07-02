import io
from datetime import datetime
import pandas as pd
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.pedido import Pedido
from app.models.conductor import PerfilConductor
from app.repositories import (
    pedido_repository, cliente_repository, historial_repository, ruta_repository, usuario_repository,
    reporte_repository, geocoding_cache_repository,
)
from app.services.geocoder import obtener_coordenadas
from app.core.codigos import asignar_codigo, generar_codigo, PREFIJO_PEDIDO

COLUMNAS_REQUERIDAS = ["direccion_destino"]


def _valor(fila, df, *nombres):
    """Primer valor no vacío entre varias columnas posibles del Excel."""
    for n in nombres:
        if n in df.columns and pd.notna(fila.get(n)):
            return fila[n]
    return None


def parsear_filas_excel(contenido: bytes, nombre_archivo: str) -> list[dict]:
    """Normaliza el Excel a lista de dicts. Recibe bytes del archivo y su nombre."""
    if not nombre_archivo.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="El archivo debe ser un Excel (.xlsx)")

    try:
        df = pd.read_excel(io.BytesIO(contenido))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error leyendo el archivo: {e}")

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
    """Crea y persiste un Pedido a partir de una fila normalizada y el cliente ya resuelto."""
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

    if geocodificar:
        lat, lng = obtener_coordenadas(pedido.direccion_destino, db)
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
    """Crea muchos pedidos en bloque con un solo flush; sin geocodificar. No hace commit."""
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
    db.flush()
    for pedido in pedidos:
        pedido.codigo = generar_codigo(PREFIJO_PEDIDO, pedido.id)
    historial_repository.registrar_bulk(
        db,
        [{"pedido_id": p.id, "estado_anterior": None, "estado_nuevo": estado, "usuario_id": usuario_id} for p in pedidos],
    )
    return pedidos


def cargar_pedidos_excel(db: Session, contenido: bytes, nombre_archivo: str, usuario_id: int | None = None) -> dict:
    """Importa pedidos desde un Excel; deduplica por referencia_externa y rechaza filas sin cliente."""
    filas = parsear_filas_excel(contenido, nombre_archivo)

    nuevos: list[Pedido] = []
    rechazados: list[dict] = []
    for i, fila in enumerate(filas):
        fila_num = i + 2  # 1 = encabezado
        referencia = fila["referencia_externa"]
        if referencia and pedido_repository.obtener_por_referencia_externa(db, referencia):
            continue

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
    """Geocodifica los pedidos sin coordenadas usando el caché de direcciones (una sola
    consulta trae las ya cacheadas, para no repetir llamadas al proveedor); marca
    GEOCODIFICACION_FALLIDA si no se encuentra la dirección."""
    pendientes = pedido_repository.obtener_sin_coordenadas(db)
    if not pendientes:
        return {"mensaje": "Todos los pedidos ya están geocodificados"}

    # Una sola consulta: coordenadas ya cacheadas de todas las direcciones del lote.
    cacheadas = geocoding_cache_repository.obtener_muchas(db, [p.direccion_destino for p in pendientes])

    exitosos = 0
    fallidos = 0

    for pedido in pendientes:
        norm = geocoding_cache_repository.normalizar(pedido.direccion_destino)
        hit = cacheadas.get(norm)
        if hit:
            lat, lng = hit
        else:
            # No estaba en caché: geocodifica (Google/Nominatim) y lo guarda para la próxima.
            lat, lng = obtener_coordenadas(pedido.direccion_destino, db)
            if lat and lng:
                cacheadas[norm] = (lat, lng)  # reutiliza si el mismo lote repite la dirección

        if lat and lng:
            pedido.latitud = lat
            pedido.longitud = lng
            partes = pedido.direccion_destino.split(",")
            pedido.distrito = partes[1].strip() if len(partes) >= 2 else "ZONA_DESCONOCIDA"
            exitosos += 1
        elif pedido.estado != "POR_RECOGER":
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
    """Devuelve {usuario_id: nombre_o_correo} para un conjunto de conductores."""
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
    """Devuelve los pedidos paginados enriquecidos con ruta y conductor asignados."""
    pedidos = pedido_repository.listar(db, skip=skip, limit=limit)
    mapa = ruta_repository.mapa_ruta_por_pedidos(db, [p.id for p in pedidos])
    nombres = _nombres_conductores(db, {cid for (_, cid) in mapa.values() if cid})
    for p in pedidos:
        ruta_nombre, conductor_id = mapa.get(p.id, (None, None))
        p.ruta_nombre = ruta_nombre
        p.conductor_nombre = nombres.get(conductor_id)
    return pedidos


def reabrir_pedido(db: Session, pedido_id: int, usuario_id: int | None = None) -> dict:
    """Devuelve un pedido FALLIDO a LISTO_PARA_ENVIO y lo saca de su ruta para reasignarlo."""
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
    """Lanza HTTP 400 si el pedido no existe o no está en estado FALLIDO."""
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    if pedido.estado != "FALLIDO":
        raise HTTPException(status_code=400, detail="Solo se pueden decidir pedidos en estado FALLIDO")


def reprogramar(db: Session, pedido_id: int, usuario_id: int | None = None) -> dict:
    """Reprograma un pedido FALLIDO: vuelve a LISTO_PARA_ENVIO y lo saca de su ruta. Recibe pedido_id y usuario_id."""
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
    """Cancela un pedido FALLIDO (estado terminal). Recibe pedido_id y usuario_id."""
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    _exigir_fallido(pedido)
    estado_anterior = pedido.estado
    ruta_repository.eliminar_detalles_de_pedido(db, pedido_id)
    pedido.estado = "CANCELADO"
    pedido.fecha_entrega = None
    historial_repository.registrar(db, pedido.id, estado_anterior, "CANCELADO", usuario_id)
    db.commit()
    reporte_repository.cerrar_abierto_de_pedido(db, pedido_id, "Cancelado", usuario_id)
    return {"mensaje": "Pedido cancelado.", "codigo": pedido.codigo}


def agrupar_por_zona(db: Session) -> dict:
    """Lista de zonas operativas con su conteo de pedidos."""
    resultados = pedido_repository.agrupar_por_zona(db)
    zonas = [{"distrito": r.distrito, "total_pedidos": r.total_pedidos} for r in resultados]
    return {"zonas_operativas": zonas}


def listar_para_ubicar(db: Session):
    """Pedidos sin coordenadas en estado resoluble, para ubicarlos manualmente en el mapa."""
    return pedido_repository.listar_sin_ubicacion_resoluble(db)


def buscar_direccion(direccion: str) -> dict:
    """Geocodifica un texto de dirección. Devuelve {encontrado, latitud, longitud}."""
    lat, lng = obtener_coordenadas((direccion or "").strip())
    if lat is None or lng is None:
        return {"encontrado": False, "latitud": None, "longitud": None}
    return {"encontrado": True, "latitud": lat, "longitud": lng}


def fijar_ubicacion(db: Session, pedido_id: int, latitud: float, longitud: float,
                    direccion: str | None = None, usuario_id: int | None = None) -> dict:
    """Fija manualmente las coordenadas de un pedido; si estaba en GEOCODIFICACION_FALLIDA lo pasa a LISTO_PARA_ENVIO."""
    pedido = pedido_repository.obtener_por_id(db, pedido_id)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    pedido.latitud = latitud
    pedido.longitud = longitud
    if direccion and direccion.strip():
        pedido.direccion_destino = direccion.strip()
    partes = (pedido.direccion_destino or "").split(",")
    pedido.distrito = partes[1].strip() if len(partes) >= 2 else "ZONA_DESCONOCIDA"

    if pedido.estado == "GEOCODIFICACION_FALLIDA":
        historial_repository.registrar(db, pedido.id, pedido.estado, "LISTO_PARA_ENVIO", usuario_id)
        pedido.estado = "LISTO_PARA_ENVIO"

    db.commit()
    return {"mensaje": "Ubicación actualizada", "codigo": pedido.codigo}


def resolver_observado(db: Session, pedido_id: int, usuario_id: int | None = None) -> dict:
    """Pasa un pedido OBSERVADO a LISTO_PARA_ENVIO una vez aclarada la discrepancia."""
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
    """Tarea en segundo plano: re-geocodifica todos los pedidos no terminales ignorando el caché."""
    from app.db.database import SessionLocal

    estados = ("POR_RECOGER", "OBSERVADO", "LISTO_PARA_ENVIO", "ASIGNADO", "EN_RUTA", "GEOCODIFICACION_FALLIDA")
    db = SessionLocal()
    try:
        pedidos = db.query(Pedido).filter(Pedido.estado.in_(estados)).all()
        pendientes_commit = 0
        for pedido in pedidos:
            lat, lng = obtener_coordenadas(pedido.direccion_destino, db, forzar=True)
            if lat and lng:
                pedido.latitud = lat
                pedido.longitud = lng
                partes = (pedido.direccion_destino or "").split(",")
                pedido.distrito = partes[1].strip() if len(partes) >= 2 else "ZONA_DESCONOCIDA"
                pendientes_commit += 1
                if pendientes_commit >= 20:   # commit por lotes
                    db.commit()
                    pendientes_commit = 0
        if pendientes_commit:
            db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
