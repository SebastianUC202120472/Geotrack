from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from app.db.database import Base


class NotificacionMecanico(Base):
    """Directorio de mecánicos y proveedores de auxilio mecánico verificados."""

    __tablename__ = "notificaciones_mecanicos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(120), nullable=False)
    empresa_taller = Column(String(150), nullable=True)
    tipo_servicio = Column(String(50), nullable=False)  # Mecánico | Grúa | Combustible | Vehículo de reemplazo | Otro
    distritos = Column(Text, nullable=False, default="")  # Distritos separados por coma: "Miraflores, Surquillo, San Isidro"
    direccion = Column(String(255), nullable=True)
    latitud = Column(Float, nullable=True)
    longitud = Column(Float, nullable=True)
    telefono_whatsapp = Column(String(30), nullable=False, unique=True, index=True)
    telegram_chat_id = Column(String(50), nullable=True, index=True)
    telefono_verificado = Column(Boolean, default=False, nullable=False)
    codigo_verificacion = Column(String(10), nullable=True)
    codigo_expira_en = Column(DateTime, nullable=True)
    horario_inicio = Column(String(10), default="08:00", nullable=False)  # HH:MM
    horario_fin = Column(String(10), default="20:00", nullable=False)     # HH:MM
    activo = Column(Boolean, default=True, nullable=False)
    creado_en = Column(DateTime, default=datetime.utcnow, nullable=False)
