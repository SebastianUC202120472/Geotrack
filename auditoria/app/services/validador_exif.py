import io
import math
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple
from PIL import Image, ExifTags

from app.core.config import settings
from app.core.registro import obtener_logger

_log = obtener_logger("validador_exif")


@dataclass
class ResultadoValidacionEXIF:
    tiene_exif: bool
    exif_fecha: Optional[datetime] = None
    exif_latitud: Optional[float] = None
    exif_longitud: Optional[float] = None
    distancia_gps_metros: Optional[float] = None
    desfase_temporal_minutos: Optional[float] = None
    alerta_gps: bool = False
    alerta_fecha: bool = False
    motivo_alerta: Optional[str] = None


def calcular_distancia_haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula la distancia geodésica en metros entre dos coordenadas (fórmula Haversine)."""
    R = 6371000.0  # Radio medio de la Tierra en metros
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def _convertir_a_grados_decimales(coordenada, referencia: str) -> Optional[float]:
    """Convierte tupla/racional (grados, minutos, segundos) de EXIF a grados decimales."""
    try:
        grados = float(coordenada[0])
        minutos = float(coordenada[1])
        segundos = float(coordenada[2])
        decimal = grados + (minutos / 60.0) + (segundos / 3600.0)
        if referencia in ("S", "W"):
            decimal = -decimal
        return decimal
    except Exception:
        return None


def extraer_exif_gps_y_fecha(datos: bytes) -> Tuple[bool, Optional[datetime], Optional[float], Optional[float]]:
    """Extrae de forma segura la fecha de captura y coordenadas GPS de los metadatos EXIF."""
    buffer = io.BytesIO(datos)
    try:
        with Image.open(buffer) as img:
            exif = img.getexif()
            if not exif:
                return False, None, None, None

            # 1. Extracción de fecha
            fecha_captura = None
            # Tags: 36867 (DateTimeOriginal), 306 (DateTime), 36868 (DateTimeDigitized)
            for tag_id in (36867, 306, 36868):
                val = exif.get(tag_id)
                if val and isinstance(val, str):
                    try:
                        # Formato EXIF estándar: "YYYY:MM:DD HH:MM:SS"
                        fecha_captura = datetime.strptime(val[:19], "%Y:%m:%d %H:%M:%S")
                        break
                    except ValueError:
                        continue

            # 2. Extracción de GPS si existe sub-IFD de GPS (tag 34853)
            gps_info = exif.get_ifd(ExifTags.IFD.GPSInfo) if hasattr(ExifTags, "IFD") else None
            latitud, longitud = None, None

            if gps_info:
                lat_raw = gps_info.get(2)  # GPSLatitude
                lat_ref = gps_info.get(1)  # GPSLatitudeRef
                lon_raw = gps_info.get(4)  # GPSLongitude
                lon_ref = gps_info.get(3)  # GPSLongitudeRef

                if lat_raw and lat_ref:
                    latitud = _convertir_a_grados_decimales(lat_raw, lat_ref)
                if lon_raw and lon_ref:
                    longitud = _convertir_a_grados_decimales(lon_raw, lon_ref)

            tiene_datos = bool(fecha_captura or (latitud is not None and longitud is not None))
            return tiene_datos, fecha_captura, latitud, longitud

    except Exception as e:
        _log.debug("Error leyendo EXIF de la imagen: %s", e)
        return False, None, None, None


def validar_exif_espaciotemporal(
    datos: bytes,
    fecha_declarada: Optional[datetime] = None,
    pedido_latitud: Optional[float] = None,
    pedido_longitud: Optional[float] = None,
    captura_gps_app: Optional[str] = None,
) -> ResultadoValidacionEXIF:
    """Valida la consistencia de fecha y ubicación de la evidencia contra el pedido.
    Si EXIF fue omitido por la cámara móvil, utiliza como respaldo el GPS capturado por la app móvil.
    """
    tiene_exif, fecha_exif, lat_exif, lon_exif = extraer_exif_gps_y_fecha(datos)

    alerta_fecha = False
    alerta_gps = False
    motivos = []
    desfase_min = None
    distancia_m = None

    # 1. Validación de Fecha
    if fecha_exif and fecha_declarada:
        diferencia_seg = abs((fecha_exif - fecha_declarada).total_seconds())
        desfase_min = round(diferencia_seg / 60.0, 1)

        if desfase_min > settings.MAX_TIME_DIFF_MINUTES:
            alerta_fecha = True
            motivos.append(
                f"Desfase horario EXIF ({desfase_min} min > {settings.MAX_TIME_DIFF_MINUTES} min permitidos)"
            )

    # 2. Validación de GPS (Prioridad: GPS incrustado en EXIF; Fallback: GPS capturado por la app móvil)
    lat_evaluar = lat_exif
    lon_evaluar = lon_exif

    if lat_evaluar is None and captura_gps_app:
        try:
            partes = captura_gps_app.split(",")
            lat_evaluar = float(partes[0].strip())
            lon_evaluar = float(partes[1].strip())
        except (ValueError, IndexError):
            pass

    if (
        lat_evaluar is not None
        and lon_evaluar is not None
        and pedido_latitud is not None
        and pedido_longitud is not None
    ):
        distancia_m = round(
            calcular_distancia_haversine(lat_evaluar, lon_evaluar, pedido_latitud, pedido_longitud),
            1,
        )
        if distancia_m > settings.MAX_GPS_DISTANCE_METERS:
            alerta_gps = True
            origen_gps = "EXIF" if lat_exif is not None else "App Móvil"
            motivos.append(
                f"Distancia excesiva de captura ({distancia_m} m según {origen_gps} > {settings.MAX_GPS_DISTANCE_METERS} m del destino)"
            )

    return ResultadoValidacionEXIF(
        tiene_exif=tiene_exif,
        exif_fecha=fecha_exif,
        exif_latitud=lat_exif,
        exif_longitud=lon_exif,
        distancia_gps_metros=distancia_m,
        desfase_temporal_minutos=desfase_min,
        alerta_gps=alerta_gps,
        alerta_fecha=alerta_fecha,
        motivo_alerta="; ".join(motivos) if motivos else None,
    )
