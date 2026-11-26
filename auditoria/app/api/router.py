import mimetypes
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core import almacenamiento
from app.db.database import get_db
from app.db import solo_lectura_core
from app.models.analisis import EvidenciaAnalisis
from app.models.revision import RevisionHumana
from app.schemas.auditoria import (
    DictamenIn,
    EvidenciaDetalleOut,
    EvidenciaResumenOut,
    MetricasOut,
    ReclamoResumenOut,
    ReincidenciaConductorOut,
    RevisionOut,
)
from app.api.deps import obtener_admin_actual
from app.services.worker_auditoria import ejecutar_ciclo_auditoria
from app.services.retencion import purgar_registros_antiguos
from app.services.demo_auditoria import sembrar_evidencias_demo

router = APIRouter(prefix="/api/auditoria", tags=["auditoria"])

_PRIORIDAD_SEMAFORO = {"rojo": 0, "ambar": 1, "verde": 2}


@router.get("/salud")
def salud_auditoria():
    """Indica al panel si el módulo de auditoría está habilitado."""
    return {
        "activo": settings.AUDITORIA_ENABLED,
        "servicio": "auditoria-evidencias",
    }


def _construir_resumen(
    analisis: EvidenciaAnalisis,
    core_info: dict,
    reclamos_count: int,
) -> EvidenciaResumenOut:
    return EvidenciaResumenOut(
        id=analisis.id,
        evidencia_id=analisis.evidencia_id,
        pedido_id=analisis.pedido_id,
        pedido_codigo=core_info.get("pedido_codigo"),
        direccion_destino=core_info.get("direccion_destino"),
        pedido_distrito=core_info.get("pedido_distrito"),
        conductor_id=core_info.get("conductor_id"),
        conductor_nombre=core_info.get("conductor_nombre"),
        semaforo=analisis.semaforo,
        motivo_alerta=analisis.motivo_alerta,
        estado_revision=analisis.estado_revision,
        calidad_score=analisis.calidad_score,
        es_duplicada=analisis.es_duplicada,
        vision_analizada=analisis.vision_analizada,
        vision_explicacion=analisis.vision_explicacion,
        tiene_reclamo=reclamos_count > 0,
        reclamos_count=reclamos_count,
        fecha_entrega=core_info.get("fecha_entrega"),
        creado_en=analisis.creado_en,
    )


@router.get("/evidencias", response_model=List[EvidenciaResumenOut])
def listar_evidencias(
    semaforo: Optional[str] = Query(default=None, pattern="^(verde|ambar|rojo)$"),
    estado_revision: Optional[str] = Query(default=None, pattern="^(PENDIENTE|VALIDA|OBSERVADA)$"),
    pedido_codigo: Optional[str] = Query(default=None, max_length=30),
    conductor_id: Optional[int] = Query(default=None),
    solo_con_reclamo: bool = Query(default=False),
    limite: int = Query(default=100, ge=1, le=300),
    _admin: dict = Depends(obtener_admin_actual),
    db: Session = Depends(get_db),
):
    """Lista la cola de evidencias auditadas con filtros, priorizando reclamos y alertas rojas."""
    consulta = db.query(EvidenciaAnalisis)
    if semaforo:
        consulta = consulta.filter(EvidenciaAnalisis.semaforo == semaforo)
    if estado_revision:
        consulta = consulta.filter(EvidenciaAnalisis.estado_revision == estado_revision)

    registros = consulta.order_by(EvidenciaAnalisis.id.desc()).limit(500).all()
    if not registros:
        return []

    ev_ids = [r.evidencia_id for r in registros]
    mapa_core = solo_lectura_core.obtener_mapa_evidencias_por_ids(db, ev_ids)
    codigos = [info.get("pedido_codigo") for info in mapa_core.values() if info.get("pedido_codigo")]
    mapa_reclamos = solo_lectura_core.obtener_conteo_reclamos_por_pedidos(db, codigos)

    filtro_cod = (pedido_codigo or "").strip().upper()
    resultados: List[EvidenciaResumenOut] = []

    for r in registros:
        info = mapa_core.get(r.evidencia_id, {})
        cod = (info.get("pedido_codigo") or "").upper()
        if filtro_cod and filtro_cod not in cod:
            continue
        if conductor_id is not None and info.get("conductor_id") != conductor_id:
            continue
        reclamos_cnt = mapa_reclamos.get(info.get("pedido_codigo") or "", 0)
        if solo_con_reclamo and reclamos_cnt == 0:
            continue
        resultados.append(_construir_resumen(r, info, reclamos_cnt))

    # Orden: primero con reclamo activo, luego rojo -> ambar -> verde, luego más reciente
    resultados.sort(
        key=lambda item: (
            0 if item.tiene_reclamo else 1,
            0 if item.estado_revision == "PENDIENTE" else 1,
            _PRIORIDAD_SEMAFORO.get(item.semaforo, 9),
            -item.id,
        )
    )
    return resultados[:limite]


@router.get("/evidencias/{analisis_id}", response_model=EvidenciaDetalleOut)
def obtener_detalle_evidencia(
    analisis_id: int,
    _admin: dict = Depends(obtener_admin_actual),
    db: Session = Depends(get_db),
):
    """Detalle completo de un análisis: métricas determinísticas, visión IA, reclamos y dictámenes."""
    analisis = db.query(EvidenciaAnalisis).filter(EvidenciaAnalisis.id == analisis_id).first()
    if not analisis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Análisis no encontrado")

    core_info = solo_lectura_core.obtener_evidencia_por_id(db, analisis.evidencia_id) or {}
    cod_pedido = core_info.get("pedido_codigo")
    reclamos_raw = solo_lectura_core.buscar_reclamos_por_pedido(db, cod_pedido) if cod_pedido else []

    revisiones = (
        db.query(RevisionHumana)
        .filter(RevisionHumana.analisis_id == analisis.id)
        .order_by(RevisionHumana.id.desc())
        .all()
    )

    return EvidenciaDetalleOut(
        id=analisis.id,
        evidencia_id=analisis.evidencia_id,
        pedido_id=analisis.pedido_id,
        pedido_codigo=cod_pedido,
        direccion_destino=core_info.get("direccion_destino"),
        pedido_distrito=core_info.get("pedido_distrito"),
        conductor_id=core_info.get("conductor_id"),
        conductor_nombre=core_info.get("conductor_nombre"),
        semaforo=analisis.semaforo,
        motivo_alerta=analisis.motivo_alerta,
        estado_revision=analisis.estado_revision,
        calidad_score=analisis.calidad_score,
        es_duplicada=analisis.es_duplicada,
        vision_analizada=analisis.vision_analizada,
        vision_explicacion=analisis.vision_explicacion,
        tiene_reclamo=len(reclamos_raw) > 0,
        reclamos_count=len(reclamos_raw),
        fecha_entrega=core_info.get("fecha_entrega"),
        creado_en=analisis.creado_en,
        es_borrosa=analisis.es_borrosa,
        varianza_laplaciana=analisis.varianza_laplaciana,
        es_oscura=analisis.es_oscura,
        es_sobreexpuesta=analisis.es_sobreexpuesta,
        brillo_promedio=analisis.brillo_promedio,
        resolucion_ancho=analisis.resolucion_ancho,
        resolucion_alto=analisis.resolucion_alto,
        tiene_exif=analisis.tiene_exif,
        exif_fecha=analisis.exif_fecha,
        distancia_gps_metros=analisis.distancia_gps_metros,
        desfase_temporal_minutos=analisis.desfase_temporal_minutos,
        alerta_gps=analisis.alerta_gps,
        alerta_fecha=analisis.alerta_fecha,
        duplicada_con_evidencia_id=analisis.duplicada_con_evidencia_id,
        distancia_hamming=analisis.distancia_hamming,
        vision_paquete=analisis.vision_paquete,
        vision_fachada=analisis.vision_fachada,
        vision_persona=analisis.vision_persona,
        vision_texto_sospechoso=analisis.vision_texto_sospechoso,
        vision_proveedor=analisis.vision_proveedor,
        receptor_nombre=core_info.get("receptor_nombre"),
        receptor_documento=core_info.get("receptor_documento"),
        latitud_longitud_captura=core_info.get("latitud_longitud_captura"),
        reclamos=[ReclamoResumenOut(**rec) for rec in reclamos_raw],
        revisiones=[
            RevisionOut(
                id=rev.id,
                admin_id=rev.admin_id,
                admin_email=rev.admin_email,
                dictamen=rev.dictamen,
                motivo=rev.motivo,
                registrado_en=rev.registrado_en,
            )
            for rev in revisiones
        ],
    )


@router.get("/evidencias/{analisis_id}/imagen")
def obtener_imagen_evidencia(
    analisis_id: int,
    _admin: dict = Depends(obtener_admin_actual),
    db: Session = Depends(get_db),
):
    """Sirve la fotografía original al administrador autenticado desde el almacenamiento :ro."""
    analisis = db.query(EvidenciaAnalisis).filter(EvidenciaAnalisis.id == analisis_id).first()
    if not analisis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Análisis no encontrado")

    contenido = almacenamiento.leer_bytes(analisis.url_foto)
    if contenido is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Archivo de imagen no disponible")

    mime = mimetypes.guess_type(analisis.url_foto)[0] or "image/jpeg"
    return Response(
        content=contenido,
        media_type=mime,
        headers={"Cache-Control": "private, max-age=300"},
    )


@router.post("/evidencias/{analisis_id}/dictamen", response_model=RevisionOut)
def registrar_dictamen_humano(
    analisis_id: int,
    payload: DictamenIn,
    admin: dict = Depends(obtener_admin_actual),
    db: Session = Depends(get_db),
):
    """Registra la decisión humana («VALIDA» u «OBSERVADA») con auditoría de usuario y fecha.
    Nunca modifica estados de pedidos en el núcleo.
    """
    analisis = db.query(EvidenciaAnalisis).filter(EvidenciaAnalisis.id == analisis_id).first()
    if not analisis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Análisis no encontrado")

    motivo_limpio = (payload.motivo or "").strip() or None
    if payload.dictamen == "OBSERVADA" and not motivo_limpio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debes indicar el motivo al marcar una evidencia como OBSERVADA",
        )

    revision = RevisionHumana(
        analisis_id=analisis.id,
        admin_id=admin["id"],
        admin_email=admin["correo"],
        dictamen=payload.dictamen,
        motivo=motivo_limpio,
        registrado_en=datetime.utcnow(),
    )
    db.add(revision)

    analisis.estado_revision = payload.dictamen
    analisis.actualizado_en = datetime.utcnow()
    db.commit()
    db.refresh(revision)

    return RevisionOut(
        id=revision.id,
        admin_id=revision.admin_id,
        admin_email=revision.admin_email,
        dictamen=revision.dictamen,
        motivo=revision.motivo,
        registrado_en=revision.registrado_en,
    )


@router.get("/metricas", response_model=MetricasOut)
def obtener_metricas(
    _admin: dict = Depends(obtener_admin_actual),
    db: Session = Depends(get_db),
):
    """Calcula KPIs de auditoría, tasa de falsas alarmas y reincidencias por conductor."""
    registros = db.query(EvidenciaAnalisis).all()
    total = len(registros)

    verde = sum(1 for r in registros if r.semaforo == "verde")
    ambar = sum(1 for r in registros if r.semaforo == "ambar")
    rojo = sum(1 for r in registros if r.semaforo == "rojo")
    pendientes = sum(1 for r in registros if r.estado_revision == "PENDIENTE")
    observadas = sum(1 for r in registros if r.estado_revision == "OBSERVADA")
    revisadas = sum(1 for r in registros if r.estado_revision in ("VALIDA", "OBSERVADA"))

    alertas_revisadas = sum(
        1 for r in registros if r.semaforo in ("ambar", "rojo") and r.estado_revision in ("VALIDA", "OBSERVADA")
    )
    falsas_alarmas = sum(
        1 for r in registros if r.semaforo in ("ambar", "rojo") and r.estado_revision == "VALIDA"
    )

    porc_observadas = round((observadas * 100.0) / total, 1) if total > 0 else 0.0
    tasa_falsas = round((falsas_alarmas * 100.0) / alertas_revisadas, 1) if alertas_revisadas > 0 else 0.0

    # Reincidencias por conductor (cruce en solo lectura)
    ev_ids = [r.evidencia_id for r in registros]
    mapa_core = solo_lectura_core.obtener_mapa_evidencias_por_ids(db, ev_ids)

    por_conductor: dict[tuple, dict] = {}
    for r in registros:
        info = mapa_core.get(r.evidencia_id, {})
        c_id = info.get("conductor_id")
        c_nom = info.get("conductor_nombre") or (f"Conductor #{c_id}" if c_id else "Sin asignar")
        llave = (c_id, c_nom)
        if llave not in por_conductor:
            por_conductor[llave] = {
                "conductor_id": c_id,
                "conductor_nombre": c_nom,
                "total_analizadas": 0,
                "total_observadas": 0,
                "total_alertas_rojas": 0,
            }
        por_conductor[llave]["total_analizadas"] += 1
        if r.estado_revision == "OBSERVADA":
            por_conductor[llave]["total_observadas"] += 1
        if r.semaforo == "rojo":
            por_conductor[llave]["total_alertas_rojas"] += 1

    reincidencias = [
        ReincidenciaConductorOut(
            **datos,
            porcentaje_observadas=round((datos["total_observadas"] * 100.0) / datos["total_analizadas"], 1)
            if datos["total_analizadas"] > 0
            else 0.0,
        )
        for datos in por_conductor.values()
    ]
    reincidencias.sort(
        key=lambda c: (-c.total_observadas, -c.total_alertas_rojas, -c.total_analizadas)
    )

    return MetricasOut(
        total_analizadas=total,
        total_verde=verde,
        total_ambar=ambar,
        total_rojo=rojo,
        pendientes_revision=pendientes,
        total_revisadas=revisadas,
        total_observadas=observadas,
        porcentaje_observadas=porc_observadas,
        falsas_alarmas=falsas_alarmas,
        tasa_falsas_alarmas=tasa_falsas,
        reincidencia_conductores=reincidencias,
    )


@router.post("/sincronizar")
def sincronizar_ahora(
    _admin: dict = Depends(obtener_admin_actual),
    db: Session = Depends(get_db),
):
    """Dispara manualmente un ciclo de detección y análisis de nuevas evidencias."""
    return ejecutar_ciclo_auditoria(db)


@router.post("/retencion/purgar")
def ejecutar_purga_retencion(
    dias: Optional[int] = Query(default=None, ge=1, le=3650),
    _admin: dict = Depends(obtener_admin_actual),
    db: Session = Depends(get_db),
):
    """Ejecuta limpieza de diagnósticos antiguos según política de retención."""
    return purgar_registros_antiguos(db, dias=dias)


@router.post("/demo")
def cargar_evidencias_demo(
    _admin: dict = Depends(obtener_admin_actual),
    db: Session = Depends(get_db),
):
    """Genera y analiza 4 evidencias de demostración (nítida, sin paquete, oscura y reciclada)."""
    return sembrar_evidencias_demo(db)
