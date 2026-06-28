# app/services/notificaciones_service.py
# Lógica de negocio para el feed de notificaciones del panel admin.
from sqlalchemy.orm import Session

from app.repositories import reporte_repository, incidencia_repository
from app.models.solicitud_recojo import SolicitudRecojo
from app.models.correo import Conversacion
from app.models.solicitud_restablecimiento import SolicitudRestablecimiento


def obtener(db: Session) -> dict:
    """Agrega los avisos accionables del admin en un solo feed. Recibe: sesión de BD."""
    reportes = reporte_repository.contar_abiertos(db)
    incidencias = incidencia_repository.contar_abiertas(db)
    recojos = db.query(SolicitudRecojo).filter(SolicitudRecojo.estado == "SOLICITADO").count()
    correos = db.query(Conversacion).filter(Conversacion.estado == "PENDIENTE").count()
    restablecimientos = db.query(SolicitudRestablecimiento).filter(SolicitudRestablecimiento.estado == "PENDIENTE").count()

    items = [
        {"tipo": "reportes", "etiqueta": "Reportes de entrega", "count": reportes, "ruta": "/pedidos"},
        {"tipo": "incidencias", "etiqueta": "Auxilio mecánico", "count": incidencias, "ruta": "/conductores"},
        {"tipo": "recojos", "etiqueta": "Solicitudes de recojo", "count": recojos, "ruta": "/bandeja"},
        {"tipo": "correos", "etiqueta": "Bandeja de correos", "count": correos, "ruta": "/bandeja"},
        {"tipo": "restablecimientos", "etiqueta": "Restablecer contraseña", "count": restablecimientos, "ruta": "/conductores"},
    ]
    # Solo se incluyen los tipos con al menos un aviso pendiente.
    items = [i for i in items if i["count"] > 0]
    return {"total": sum(i["count"] for i in items), "items": items}
