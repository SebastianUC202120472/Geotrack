# app/services/liquidacion_service.py
# CUS-36: genera el reporte de liquidación de un cliente en Excel (.xlsx), lo guarda
# en /media y registra el documento en la tabla 'liquidaciones' para tener historial.
import os
import re
import secrets
from datetime import datetime, date
from typing import Optional

from fastapi import HTTPException, status
from openpyxl import Workbook
from openpyxl.styles import Font
from sqlalchemy.orm import Session

from app.repositories import pedido_repository, ruta_repository, cliente_repository, liquidacion_repository

# Carpeta PRIVADA de los .xlsx generados. A propósito NO está bajo 'uploads/' (que se
# sirve público en /media): la liquidación contiene datos personales de muchos
# destinatarios (Ley 29733) y solo se descarga por un endpoint autenticado de admin.
DIR_LIQUIDACIONES = os.path.join("archivos_privados", "liquidaciones")

# Encabezados del reporte (orden de columnas del Excel).
COLUMNAS = [
    "Código", "Referencia", "Cliente", "Destinatario", "Dirección",
    "Distrito", "Estado", "Fecha de entrega", "Motivo de fallo",
]


def _slug(texto: str) -> str:
    """Convierte un nombre en un fragmento seguro para nombre de archivo. Recibe: texto."""
    limpio = re.sub(r"[^A-Za-z0-9]+", "_", (texto or "cliente").strip())
    return limpio.strip("_").lower() or "cliente"


def generar(db: Session, cliente: str, periodo_inicio: Optional[date], periodo_fin: Optional[date]) -> dict:
    """CUS-36: arma la liquidación (entregados y fallidos) de un cliente y la persiste.
    Recibe: el nombre del cliente (cliente_origen) y un rango de fechas opcional.
    Devuelve: metadata con la URL del .xlsx descargable y el total de pedidos."""
    # Solo se liquidan los pedidos con resultado de reparto (entregados y fallidos): los que
    # siguen en proceso (POR_RECOGER, LISTO_PARA_ENVIO, ASIGNADO, EN_RUTA, OBSERVADO) o
    # CANCELADO no representan un servicio prestado y no deben inflar el total facturable.
    pedidos = pedido_repository.listar_por_cliente(
        db, cliente, periodo_inicio, periodo_fin, estados=("ENTREGADO", "FALLIDO")
    )
    if not pedidos:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No hay pedidos entregados o fallidos del cliente '{cliente}' para liquidar",
        )

    # Construcción del Excel: una fila por pedido con su estado y, si falló, el motivo.
    wb = Workbook()
    hoja = wb.active
    hoja.title = "Liquidación"
    hoja.append(COLUMNAS)
    for celda in hoja[1]:
        celda.font = Font(bold=True)

    for pedido in pedidos:
        motivo = None
        par = ruta_repository.obtener_detalle_y_ruta_por_pedido(db, pedido.id)
        if par:
            detalle, _ = par
            motivo = detalle.motivo_fallo
        fecha_entrega = pedido.fecha_entrega.strftime("%Y-%m-%d %H:%M") if pedido.fecha_entrega else ""
        hoja.append([
            pedido.codigo or "",
            pedido.referencia_externa or "",
            pedido.cliente_origen or "",
            pedido.nombre_destinatario or "",
            pedido.direccion_destino or "",
            pedido.distrito or "",
            pedido.estado or "",
            fecha_entrega,
            motivo or "",
        ])

    # Guardado físico en la carpeta privada. El nombre lleva un token aleatorio fuerte
    # (no adivinable/enumerable) además del cliente, por defensa en profundidad.
    os.makedirs(DIR_LIQUIDACIONES, exist_ok=True)
    nombre_final = f"liquidacion_{_slug(cliente)}_{secrets.token_hex(16)}.xlsx"
    ruta_fisica = os.path.join(DIR_LIQUIDACIONES, nombre_final)
    wb.save(ruta_fisica)

    # Si el cliente está registrado como empresa formal, enlazamos su id (diagrama).
    registro = cliente_repository.obtener_por_razon_social(db, cliente)
    cliente_id = registro.id if registro else None

    # En la BD guardamos la RUTA EN DISCO (privada), no una URL pública.
    liquidacion = liquidacion_repository.crear(db, cliente_id, periodo_inicio, periodo_fin, ruta_fisica)

    # La descarga se hace por un endpoint autenticado de admin (no por /media).
    return {
        "mensaje": "Liquidación generada correctamente",
        "cliente": cliente,
        "total_pedidos": len(pedidos),
        "liquidacion_id": liquidacion.id,
        "descarga_url": f"/dashboard/liquidaciones/{liquidacion.id}/descarga",
        "archivo": nombre_final,
    }


def ruta_archivo(db: Session, liquidacion_id: int) -> tuple[str, str]:
    """Devuelve (ruta_en_disco, nombre_descarga) de una liquidación para el endpoint
    autenticado de descarga. Recibe: el id. Lanza 404 si no existe o el archivo se perdió."""
    liquidacion = liquidacion_repository.obtener_por_id(db, liquidacion_id)
    if liquidacion is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Liquidación no encontrada")
    ruta = liquidacion.url_documento
    if not ruta or not os.path.exists(ruta):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El archivo de la liquidación ya no está disponible; vuelve a generarla.",
        )
    return ruta, os.path.basename(ruta)
