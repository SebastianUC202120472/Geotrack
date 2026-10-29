import os
import re
import secrets
from datetime import datetime, date
from typing import Optional

from fastapi import HTTPException, status
from openpyxl import Workbook
from openpyxl.styles import Font
from sqlalchemy.orm import Session

import io

from app.core import almacenamiento
from app.core.excel import fila_segura
from app.repositories import pedido_repository, ruta_repository, cliente_repository, liquidacion_repository

# Carpeta privada para .xlsx; no bajo /media para evitar acceso público.

COLUMNAS = [
    "Código", "Referencia", "Cliente", "Destinatario", "Dirección",
    "Distrito", "Estado", "Fecha de entrega", "Motivo de fallo",
]


def _slug(texto: str) -> str:
    """Convierte texto en fragmento seguro para nombre de archivo."""
    limpio = re.sub(r"[^A-Za-z0-9]+", "_", (texto or "cliente").strip())
    return limpio.strip("_").lower() or "cliente"


def generar(db: Session, cliente: str, periodo_inicio: Optional[date], periodo_fin: Optional[date]) -> dict:
    """Genera la liquidacion Excel de un cliente (entregados y fallidos) y la persiste. Recibe nombre del cliente y rango de fechas."""
    pedidos = pedido_repository.listar_por_cliente(
        db, cliente, periodo_inicio, periodo_fin, estados=("ENTREGADO", "FALLIDO")
    )
    if not pedidos:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No hay pedidos entregados o fallidos del cliente '{cliente}' para liquidar",
        )

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
        hoja.append(fila_segura([
            pedido.codigo or "",
            pedido.referencia_externa or "",
            pedido.cliente_origen or "",
            pedido.nombre_destinatario or "",
            pedido.direccion_destino or "",
            pedido.distrito or "",
            pedido.estado or "",
            fecha_entrega,
            motivo or "",
        ]))

    nombre_final = f"liquidacion_{_slug(cliente)}_{secrets.token_hex(16)}.xlsx"
    buffer = io.BytesIO()
    wb.save(buffer)
    # Se guarda en "privado/": la descarga va solo por el endpoint autenticado, nunca por /media.
    clave = f"{almacenamiento.CARPETA_PRIVADA}liquidaciones/{nombre_final}"
    almacenamiento.guardar(clave, buffer.getvalue())

    registro = cliente_repository.obtener_por_razon_social(db, cliente)
    cliente_id = registro.id if registro else None

    liquidacion = liquidacion_repository.crear(db, cliente_id, periodo_inicio, periodo_fin, clave)
    liquidacion.cliente_nombre = cliente
    liquidacion.total_pedidos = len(pedidos)
    db.commit()

    return {
        "mensaje": "Liquidación generada correctamente",
        "cliente": cliente,
        "total_pedidos": len(pedidos),
        "liquidacion_id": liquidacion.id,
        "descarga_url": f"/dashboard/liquidaciones/{liquidacion.id}/descarga",
        "archivo": nombre_final,
    }


def historial(db: Session) -> list:
    """Liquidaciones ya generadas para volver a descargarlas (C36-02). Recibe la sesion."""
    return [
        {
            "id": l.id, "cliente": l.cliente_nombre or "—", "total_pedidos": l.total_pedidos,
            "periodo_inicio": l.periodo_inicio, "periodo_fin": l.periodo_fin, "generada_en": l.fecha_generacion,
            "descarga_url": f"/dashboard/liquidaciones/{l.id}/descarga",
            "disponible": _existe(l.url_documento),
        }
        for l in liquidacion_repository.listar(db)  # noqa: E741
    ]


def _leer_documento(referencia: str | None) -> bytes | None:
    """Bytes de la liquidacion. Las nuevas guardan la clave del almacenamiento; las anteriores
    a EX-08, la ruta en disco (archivos_privados/...). Recibe la referencia guardada."""
    if not referencia:
        return None
    if referencia.startswith(almacenamiento.CARPETA_PRIVADA):
        return almacenamiento.leer(referencia)
    if os.path.isfile(referencia):
        with open(referencia, "rb") as f:
            return f.read()
    return None


def _existe(referencia: str | None) -> bool:
    """True si el archivo de la liquidacion sigue disponible. Recibe la referencia guardada."""
    if not referencia:
        return False
    if referencia.startswith(almacenamiento.CARPETA_PRIVADA):
        return almacenamiento.existe(referencia)
    return os.path.isfile(referencia)


def contenido_archivo(db: Session, liquidacion_id: int) -> tuple[bytes, str]:
    """Devuelve (bytes, nombre_archivo) de una liquidacion. Recibe: liquidacion_id."""
    liquidacion = liquidacion_repository.obtener_por_id(db, liquidacion_id)
    if liquidacion is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Liquidación no encontrada")
    contenido = _leer_documento(liquidacion.url_documento)
    if contenido is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El archivo de la liquidación ya no está disponible; vuelve a generarla.",
        )
    return contenido, os.path.basename(liquidacion.url_documento)
