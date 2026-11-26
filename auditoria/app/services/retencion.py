from datetime import datetime, timedelta
from typing import Dict
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.registro import obtener_logger
from app.models.analisis import EvidenciaAnalisis
from app.models.cola import ColaTrabajo

_log = obtener_logger("retencion")


def purgar_registros_antiguos(db: Session, dias: int | None = None) -> Dict[str, int]:
    """Elimina análisis propios y tareas de cola antiguos según la política de retención.
    Nunca modifica tablas ni archivos del núcleo de GeoTrack.
    """
    ventana_dias = max(1, dias if dias is not None else settings.AUDITORIA_RETENCION_DIAS)
    corte = datetime.utcnow() - timedelta(days=ventana_dias)

    analisis_antiguos = db.query(EvidenciaAnalisis).filter(EvidenciaAnalisis.creado_en < corte).all()
    eliminados_analisis = len(analisis_antiguos)
    for item in analisis_antiguos:
        db.delete(item)  # Cascade elimina también RevisionHumana asociada

    eliminados_cola = (
        db.query(ColaTrabajo)
        .filter(ColaTrabajo.creado_en < corte, ColaTrabajo.estado.in_(("COMPLETADO", "FALLIDO", "OMITIDO_TOPE")))
        .delete(synchronize_session=False)
    )

    db.commit()
    if eliminados_analisis or eliminados_cola:
        _log.info(
            "Política de retención (%d días): %d análisis y %d tareas de cola eliminadas.",
            ventana_dias,
            eliminados_analisis,
            eliminados_cola,
        )

    return {
        "dias_retencion": ventana_dias,
        "analisis_eliminados": eliminados_analisis,
        "cola_eliminada": eliminados_cola,
    }
