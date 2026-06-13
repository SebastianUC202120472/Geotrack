# app/services/pedido_service.py
# ============================================================================
# CAPA: SERVICIO (lógica de negocio) — Clean Architecture
# ----------------------------------------------------------------------------
# ¿QUÉ HACE?  La inteligencia del módulo Inbound:
#               - CUS-13: leer el Excel, crear/enlazar el CLIENTE, guardar el
#                 DESTINATARIO y registrar el primer evento de trazabilidad.
#               - CUS-15: geocodificar (dirección -> latitud/longitud).
#               - CUS-16: agrupar pedidos por distrito.
# ¿CON QUÉ SE CONECTA?
#   - repositories/pedido_repository.py    -> lectura/escritura de pedidos.
#   - repositories/cliente_repository.py   -> crea/enlaza la empresa cliente.
#   - repositories/historial_repository.py -> registra eventos (CUS-35).
#   - services/geocoder.py                 -> coordenadas desde la dirección.
#   - Lo USA: api/pedidos.py.
# ============================================================================
import io
import pandas as pd
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.pedido import Pedido
from app.repositories import pedido_repository, cliente_repository, historial_repository
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

    # 4) Construir los pedidos nuevos.
    nuevos: list[Pedido] = []
    for _, fila in df.iterrows():
        # Referencia externa: el id que trae el Excel (opcional). NO es el tracking;
        # nuestro tracking será el código PD-001 que generamos abajo.
        referencia = _str_o_none(_valor(fila, df, "referencia_externa", "numero_tracking", "id"))
        if referencia and pedido_repository.obtener_por_referencia_externa(db, referencia):
            continue  # ya se importó antes -> no duplicar

        # Cliente (empresa que envía): se busca o se crea automáticamente.
        razon = str(_valor(fila, df, "razon_social_cliente", "cliente_origen"))
        ruc = _valor(fila, df, "ruc_cliente", "identificador_unico")
        ruc = str(ruc) if ruc is not None else None
        cliente = cliente_repository.buscar_o_crear(db, razon_social=razon, identificador_unico=ruc)

        peso = _valor(fila, df, "peso_kg")
        volumen = _valor(fila, df, "volumen_m3")

        nuevos.append(
            Pedido(
                referencia_externa=referencia,
                cliente_id=cliente.id,
                cliente_origen=razon,  # snapshot del nombre del cliente
                direccion_destino=str(fila["direccion_destino"]),
                # Destinatario (persona que recibe), todos opcionales:
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


def listar_pedidos(db: Session, skip: int, limit: int):
    """Devuelve los pedidos paginados (panel web del admin)."""
    return pedido_repository.listar(db, skip=skip, limit=limit)


def agrupar_por_zona(db: Session) -> dict:
    """CUS-16: arma la lista de zonas operativas con su conteo de pedidos."""
    resultados = pedido_repository.agrupar_por_zona(db)
    zonas = [{"distrito": r.distrito, "total_pedidos": r.total_pedidos} for r in resultados]
    return {"zonas_operativas": zonas}
