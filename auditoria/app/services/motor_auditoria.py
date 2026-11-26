from datetime import datetime
from typing import Optional
import httpx
from sqlalchemy.orm import Session

from app.core.registro import obtener_logger
from app.models.analisis import EvidenciaAnalisis
from app.services.validador_archivo import validar_archivo_seguro
from app.services.calidad_imagen import evaluar_calidad_imagen
from app.services.hash_perceptual import (
    calcular_sha256,
    calcular_perceptual_hash,
    buscar_foto_reciclada,
)
from app.services.validador_exif import validar_exif_espaciotemporal
from app.ia.prompt_vision import EvaluacionVision
from app.ia.cliente_vision import analizar_imagen_con_fallback

_log = obtener_logger("motor_auditoria")


def _obtener_o_crear_analisis(
    db: Session,
    evidencia_id: int,
    pedido_id: int,
    url_foto: str,
) -> EvidenciaAnalisis:
    """Obtiene el análisis existente para (evidencia_id, url_foto) o crea uno nuevo (idempotente)."""
    analisis = db.query(EvidenciaAnalisis).filter(
        EvidenciaAnalisis.evidencia_id == evidencia_id,
        EvidenciaAnalisis.url_foto == url_foto,
    ).first()
    if not analisis:
        analisis = EvidenciaAnalisis(
            evidencia_id=evidencia_id,
            pedido_id=pedido_id,
            url_foto=url_foto,
        )
        db.add(analisis)
    return analisis


def procesar_auditoria_deterministica(
    db: Session,
    evidencia_id: int,
    pedido_id: int,
    url_foto: str,
    datos_imagen: bytes,
    fecha_entrega_declarada: Optional[datetime] = None,
    pedido_latitud: Optional[float] = None,
    pedido_longitud: Optional[float] = None,
    captura_gps_app: Optional[str] = None,
) -> EvidenciaAnalisis:
    """Ejecuta el análisis determinístico completo sobre una evidencia fotográfica.
    Si falla filtros críticos (corrupto, bomba, borroso extremo, oscuro, reciclado),
    asigna semáforo 'rojo' o 'ambar' y habilita cortocircuito antes de consultar modelos de IA.
    """
    motivos_alerta = []
    semaforo = "verde"

    # 1. Validación segura del archivo (Magic bytes, tamaño, bomba de descompresión)
    val_archivo = validar_archivo_seguro(datos_imagen)
    if not val_archivo.valido:
        _log.warning("Evidencia %d rechazada en validación de archivo: %s", evidencia_id, val_archivo.error)
        analisis = _obtener_o_crear_analisis(db, evidencia_id, pedido_id, url_foto)
        analisis.sha256 = calcular_sha256(datos_imagen) if datos_imagen else "invalido"
        analisis.calidad_score = 0.0
        analisis.semaforo = "rojo"
        analisis.motivo_alerta = f"Archivo no seguro o inválido: {val_archivo.error}"
        analisis.estado_revision = analisis.estado_revision or "PENDIENTE"
        analisis.actualizado_en = datetime.utcnow()
        db.commit()
        db.refresh(analisis)
        return analisis

    # 2. Evaluación de Calidad de Imagen (Pillow: borrosidad, luminosidad, resolución)
    calidad = evaluar_calidad_imagen(datos_imagen)
    if calidad.advertencias:
        motivos_alerta.extend(calidad.advertencias)

    # 3. Hashes criptográfico y perceptual (ImageHash / dHash) + Detección de Reciclaje
    sha256_val = calcular_sha256(datos_imagen)
    p_hash = calcular_perceptual_hash(datos_imagen)
    es_dup, dup_id, dist_h = buscar_foto_reciclada(
        db,
        hash_perceptual=p_hash,
        sha256_actual=sha256_val,
        evidencia_id_actual=evidencia_id,
    )

    if es_dup:
        motivos_alerta.append(
            f"Foto reciclada/duplicada (coincide con evidencia previa {dup_id}, distancia Hamming: {dist_h})"
        )

    # 4. Metadatos EXIF y Validación Espaciotemporal (Fecha y GPS)
    exif = validar_exif_espaciotemporal(
        datos=datos_imagen,
        fecha_declarada=fecha_entrega_declarada,
        pedido_latitud=pedido_latitud,
        pedido_longitud=pedido_longitud,
        captura_gps_app=captura_gps_app,
    )
    if exif.motivo_alerta:
        motivos_alerta.append(exif.motivo_alerta)

    # 5. Determinación del Semáforo Preliminar (Determinístico)
    # ROJO: Duplicado confirmado, foto negra/oscura extrema, o resolución pésima
    if es_dup or (calidad.es_oscura and calidad.brillo_promedio < 25.0) or calidad.calidad_score < 0.35:
        semaforo = "rojo"
    # AMBAR: Borrosa, desfase GPS > 350m, o alerta de fecha EXIF
    elif calidad.es_borrosa or calidad.es_oscura or calidad.es_sobreexpuesta or exif.alerta_gps or exif.alerta_fecha:
        semaforo = "ambar"
    else:
        semaforo = "verde"

    motivo_str = " | ".join(motivos_alerta) if motivos_alerta else None

    # Guardar o actualizar registro de análisis en el esquema auditoria
    analisis = _obtener_o_crear_analisis(db, evidencia_id, pedido_id, url_foto)

    analisis.sha256 = sha256_val
    analisis.perceptual_hash = p_hash
    analisis.calidad_score = calidad.calidad_score
    analisis.es_borrosa = calidad.es_borrosa
    analisis.varianza_laplaciana = calidad.varianza_laplaciana
    analisis.es_oscura = calidad.es_oscura
    analisis.es_sobreexpuesta = calidad.es_sobreexpuesta
    analisis.brillo_promedio = calidad.brillo_promedio
    analisis.resolucion_ancho = calidad.resolucion_ancho
    analisis.resolucion_alto = calidad.resolucion_alto

    analisis.tiene_exif = exif.tiene_exif
    analisis.exif_fecha = exif.exif_fecha
    analisis.exif_latitud = exif.exif_latitud
    analisis.exif_longitud = exif.exif_longitud
    analisis.distancia_gps_metros = exif.distancia_gps_metros
    analisis.desfase_temporal_minutos = exif.desfase_temporal_minutos
    analisis.alerta_gps = exif.alerta_gps
    analisis.alerta_fecha = exif.alerta_fecha

    analisis.es_duplicada = es_dup
    analisis.duplicada_con_evidencia_id = dup_id
    analisis.distancia_hamming = dist_h

    analisis.semaforo = semaforo
    analisis.motivo_alerta = motivo_str
    analisis.actualizado_en = datetime.utcnow()

    db.commit()
    db.refresh(analisis)
    return analisis


def debe_consultar_ia(analisis: EvidenciaAnalisis) -> bool:
    """Cortocircuito determinístico: evita gastar cuota de IA si la foto ya falló filtros críticos."""
    if analisis.calidad_score <= 0.0:
        return False
    if analisis.es_duplicada:
        return False
    if analisis.es_oscura and (analisis.brillo_promedio or 0.0) < 25.0:
        return False
    if analisis.calidad_score < 0.35:
        return False
    return True


def aplicar_evaluacion_vision(
    db: Session,
    analisis: EvidenciaAnalisis,
    evaluacion: Optional[EvaluacionVision],
    proveedor: Optional[str],
) -> EvidenciaAnalisis:
    """Combina determinísticamente en Python las señales de visión IA con los filtros previos.
    El semáforo final nunca es elegido por el LLM directamente (defensa OWASP LLM01).
    """
    if evaluacion is None:
        return analisis

    analisis.vision_analizada = True
    analisis.vision_paquete = evaluacion.hay_paquete
    analisis.vision_fachada = evaluacion.hay_puerta_o_fachada
    analisis.vision_persona = evaluacion.hay_persona_recibiendo
    analisis.vision_texto_sospechoso = evaluacion.texto_sospechoso_en_imagen
    analisis.vision_explicacion = evaluacion.explicacion_breve
    analisis.vision_proveedor = proveedor

    motivos_previos = [m.strip() for m in (analisis.motivo_alerta or "").split("|") if m.strip()]
    semaforo = analisis.semaforo

    if evaluacion.texto_sospechoso_en_imagen:
        motivos_previos.append("Posible intento de manipulación por texto en imagen (OWASP LLM01)")
        semaforo = "rojo"
    elif not evaluacion.hay_paquete and not evaluacion.hay_puerta_o_fachada and not evaluacion.hay_persona_recibiendo:
        motivos_previos.append("IA no distingue paquete, fachada ni persona en la foto")
        semaforo = "rojo"
    elif not evaluacion.hay_paquete:
        motivos_previos.append("IA no distingue claramente el paquete entregado")
        if semaforo == "verde":
            semaforo = "ambar"
    elif not evaluacion.hay_puerta_o_fachada and not evaluacion.hay_persona_recibiendo:
        motivos_previos.append("IA distingue paquete pero sin contexto de domicilio o receptor")
        if semaforo == "verde":
            semaforo = "ambar"

    # Eliminar duplicados preservando orden
    motivos_unicos = list(dict.fromkeys(motivos_previos))
    analisis.semaforo = semaforo
    analisis.motivo_alerta = " | ".join(motivos_unicos) if motivos_unicos else None
    analisis.actualizado_en = datetime.utcnow()

    db.commit()
    db.refresh(analisis)
    return analisis


def procesar_auditoria_completa(
    db: Session,
    evidencia_id: int,
    pedido_id: int,
    url_foto: str,
    datos_imagen: bytes,
    fecha_entrega_declarada: Optional[datetime] = None,
    pedido_latitud: Optional[float] = None,
    pedido_longitud: Optional[float] = None,
    captura_gps_app: Optional[str] = None,
    http_client: Optional[httpx.Client] = None,
) -> EvidenciaAnalisis:
    """Pipeline completo Semana 13 + Semana 14:
    1. Ejecuta filtros determinísticos.
    2. Si supera el cortocircuito, consulta Visión IA con fallback.
    3. Calcula en Python el semáforo combinado final.
    """
    analisis = procesar_auditoria_deterministica(
        db=db,
        evidencia_id=evidencia_id,
        pedido_id=pedido_id,
        url_foto=url_foto,
        datos_imagen=datos_imagen,
        fecha_entrega_declarada=fecha_entrega_declarada,
        pedido_latitud=pedido_latitud,
        pedido_longitud=pedido_longitud,
        captura_gps_app=captura_gps_app,
    )

    if debe_consultar_ia(analisis):
        evaluacion, proveedor = analizar_imagen_con_fallback(datos_imagen, http_client=http_client)
        analisis = aplicar_evaluacion_vision(db, analisis, evaluacion, proveedor)

    return analisis
