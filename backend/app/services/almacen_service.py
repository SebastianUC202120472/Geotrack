# app/services/almacen_service.py
# Lógica del módulo de almacén (CUS-14): importar trama, escanear contra ella,
# conciliar y cerrar el ingreso de un recojo.
import io
from datetime import datetime

import pandas as pd
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories import almacen_repository, recojo_repository
from app.schemas.almacen import (
    ConteoConciliacion,
    TramaImportResponse,
    EscaneoResponse,
    ConciliacionResponse,
    PaqueteEsperadoItem,
    RecojoAlmacenItem,
    CerrarIngresoResponse,
)

# Un recojo se ingresa cuando ya fue recogido; INGRESADO permite reabrir/reescanear.
ESTADOS_INGRESABLES = ("RECOGIDO", "INGRESADO")
# Nombres de columna aceptados para el código en el Excel de la trama.
COLUMNAS_CODIGO = ["codigo", "codigo_rastreo", "tracking", "numero_tracking"]


def _recojo_ingresable(db: Session, recojo_id: int):
    """Devuelve el recojo si existe y está en un estado ingresable; si no, 404/400."""
    recojo = recojo_repository.obtener_por_id(db, recojo_id)
    if not recojo:
        raise HTTPException(status_code=404, detail="Recojo no encontrado")
    if recojo.estado not in ESTADOS_INGRESABLES:
        raise HTTPException(status_code=400, detail=f"El recojo debe estar RECOGIDO para ingresarlo (estado: {recojo.estado})")
    return recojo


def _conteo(db: Session, recojo_id: int) -> ConteoConciliacion:
    """Arma el resumen de conciliación de un recojo."""
    esperados, ingresados, desconocidos = almacen_repository.contar(db, recojo_id)
    return ConteoConciliacion(
        esperados=esperados, ingresados=ingresados,
        faltantes=esperados - ingresados, desconocidos=desconocidos,
    )


def importar_trama(db: Session, recojo_id: int, contenido: bytes, nombre_archivo: str, usuario_id: int | None) -> TramaImportResponse:
    """Importa la trama (códigos esperados) de un recojo desde un Excel. Recibe: id, bytes y nombre."""
    _recojo_ingresable(db, recojo_id)
    if not nombre_archivo.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="El archivo debe ser un Excel (.xlsx)")
    try:
        df = pd.read_excel(io.BytesIO(contenido))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error leyendo el archivo: {e}")

    columna = next((c for c in COLUMNAS_CODIGO if c in df.columns), None)
    if not columna:
        raise HTTPException(status_code=400, detail=f"El Excel debe tener una columna de código ({', '.join(COLUMNAS_CODIGO)})")

    codigos = [str(v).strip() for v in df[columna].dropna().tolist() if str(v).strip()]
    importados, duplicados = almacen_repository.agregar_esperados(db, recojo_id, codigos)
    almacen_repository.guardar_cambios(db)

    total = almacen_repository.contar(db, recojo_id)[0]
    return TramaImportResponse(
        recojo_id=recojo_id, importados=importados, duplicados=duplicados, total_trama=total,
        mensaje=f"Trama importada: {importados} nuevos, {duplicados} duplicados ignorados",
    )


def escanear(db: Session, recojo_id: int, codigo: str, usuario_id: int | None) -> EscaneoResponse:
    """Cruza un código escaneado contra la trama del recojo. Recibe: id, código y usuario."""
    _recojo_ingresable(db, recojo_id)
    codigo = (codigo or "").strip()
    if not codigo:
        raise HTTPException(status_code=400, detail="El código no puede estar vacío")
    if almacen_repository.contar(db, recojo_id)[0] == 0:
        raise HTTPException(status_code=400, detail="Primero importa la trama del recojo")

    esperado = almacen_repository.obtener_esperado(db, recojo_id, codigo)
    if esperado is None:
        # No está en la trama: lo registramos como desconocido (sin duplicar).
        if not almacen_repository.obtener_desconocido(db, recojo_id, codigo):
            almacen_repository.agregar_desconocido(db, recojo_id, codigo, usuario_id)
            almacen_repository.guardar_cambios(db)
        return EscaneoResponse(resultado="DESCONOCIDO", codigo=codigo, mensaje="El código no está en la trama de este recojo", conteo=_conteo(db, recojo_id))

    if esperado.estado == "INGRESADO":
        return EscaneoResponse(resultado="DUPLICADO", codigo=codigo, mensaje="Este paquete ya fue ingresado", conteo=_conteo(db, recojo_id))

    esperado.estado = "INGRESADO"
    esperado.escaneado_en = datetime.utcnow()
    esperado.escaneado_por = usuario_id
    almacen_repository.guardar_cambios(db)
    return EscaneoResponse(resultado="INGRESADO", codigo=codigo, mensaje="Paquete ingresado correctamente", conteo=_conteo(db, recojo_id))


def cerrar_ingreso(db: Session, recojo_id: int, usuario_id: int | None) -> CerrarIngresoResponse:
    """Cierra el ingreso: el recojo pasa a INGRESADO (permitido aun con faltantes)."""
    recojo = _recojo_ingresable(db, recojo_id)
    recojo.estado = "INGRESADO"
    almacen_repository.guardar_cambios(db)
    return CerrarIngresoResponse(recojo_id=recojo_id, estado=recojo.estado, conteo=_conteo(db, recojo_id), mensaje="Ingreso cerrado")


def obtener_conciliacion(db: Session, recojo_id: int) -> ConciliacionResponse:
    """Conciliación detallada de un recojo (trama + desconocidos + conteo)."""
    recojo = recojo_repository.obtener_por_id(db, recojo_id)
    if not recojo:
        raise HTTPException(status_code=404, detail="Recojo no encontrado")
    esperados = [
        PaqueteEsperadoItem(codigo=e.codigo, estado=e.estado, escaneado_en=e.escaneado_en)
        for e in almacen_repository.listar_esperados(db, recojo_id)
    ]
    desconocidos = [d.codigo for d in almacen_repository.listar_desconocidos(db, recojo_id)]
    return ConciliacionResponse(
        recojo_id=recojo_id, estado_recojo=recojo.estado, conteo=_conteo(db, recojo_id),
        esperados=esperados, desconocidos=desconocidos,
    )


def listar_recojos(db: Session, estado: str | None = None) -> list:
    """Lista los recojos del módulo de almacén (por defecto RECOGIDO + INGRESADO) con su conteo."""
    estados = [estado] if estado else ["RECOGIDO", "INGRESADO"]
    items = []
    for e in estados:
        for r in recojo_repository.listar(db, e):
            items.append(RecojoAlmacenItem(
                id=r.id, codigo=r.codigo, cliente_origen=r.cliente_origen, estado=r.estado,
                cantidad_declarada=r.cantidad_declarada, conteo=_conteo(db, r.id),
            ))
    return items
