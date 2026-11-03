from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from app.db.database import Base


class NotificacionEnvio(Base):
    """Cola de avisos automaticos: cada fila es un mensaje creado en el momento justo.
    El estado dice si ya se envio; la clave unica evita duplicados aunque el servicio se reinicie."""

    __tablename__ = "notificaciones_envios"

    id = Column(Integer, primary_key=True, index=True)
    notificacion_id = Column(Integer, ForeignKey("notificaciones.id"), nullable=True, index=True)
    evento = Column(String(40))                       # PEDIDO_ENTREGADO, AUXILIO_MECANICO, ...
    canal = Column(String(20))                        # telegram | correo
    destinatario_tipo = Column(String(30))            # destinatario | cliente_corporativo | almacen | administrador | mecanico | conductor
    destinatario_valor = Column(String(120))          # telefono o correo
    destinatario_nombre = Column(String(120), nullable=True)
    asunto = Column(String(200), nullable=True)       # solo correo
    cuerpo = Column(Text, nullable=False)
    prioridad = Column(String(10), default="normal")  # normal | urgente
    estado = Column(String(10), default="PENDIENTE")  # PENDIENTE | ENVIADO | FALLIDO
    clave_idempotencia = Column(String(120), unique=True, index=True)  # evento:destinatario:codigo
    programada_para = Column(DateTime, nullable=True)  # horario silencioso / resumen del dia
    intentos = Column(Integer, default=0)
    bloqueado_hasta = Column(DateTime, nullable=True)
    worker_id = Column(String(80), nullable=True)
    proximo_intento_en = Column(DateTime, nullable=True)
    creado_en = Column(DateTime, default=datetime.utcnow, index=True)
    enviado_en = Column(DateTime, nullable=True)
    detalle = Column(String(255), nullable=True)
