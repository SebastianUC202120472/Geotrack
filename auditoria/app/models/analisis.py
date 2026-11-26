from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.orm import relationship

from app.db.database import Base


class EvidenciaAnalisis(Base):
    """Resultado del análisis determinístico y de visión con IA sobre una evidencia de entrega."""

    __tablename__ = "analisis_evidencias"

    id = Column(Integer, primary_key=True, index=True)
    evidencia_id = Column(Integer, nullable=False, index=True)      # ID en public.evidencias_entrega
    pedido_id = Column(Integer, nullable=False, index=True)         # ID en public.pedidos
    url_foto = Column(String(255), nullable=False)                  # URL de la foto analizada
    sha256 = Column(String(64), nullable=False, index=True)         # Hash criptográfico de los bytes
    perceptual_hash = Column(String(64), nullable=True, index=True) # pHash / dHash para detectar duplicados

    # Métricas de Calidad (Pillow)
    calidad_score = Column(Float, nullable=False, default=1.0)      # 0.0 (pésima) a 1.0 (excelente)
    es_borrosa = Column(Boolean, nullable=False, default=False)
    varianza_laplaciana = Column(Float, nullable=True)
    es_oscura = Column(Boolean, nullable=False, default=False)
    es_sobreexpuesta = Column(Boolean, nullable=False, default=False)
    brillo_promedio = Column(Float, nullable=True)
    resolucion_ancho = Column(Integer, nullable=True)
    resolucion_alto = Column(Integer, nullable=True)

    # Metadatos EXIF y Validación Espaciotemporal
    tiene_exif = Column(Boolean, nullable=False, default=False)
    exif_fecha = Column(DateTime, nullable=True)
    exif_latitud = Column(Float, nullable=True)
    exif_longitud = Column(Float, nullable=True)
    distancia_gps_metros = Column(Float, nullable=True)             # Distancia entre GPS captura y destino
    desfase_temporal_minutos = Column(Float, nullable=True)         # Diferencia entre hora EXIF y hora entrega
    alerta_gps = Column(Boolean, nullable=False, default=False)
    alerta_fecha = Column(Boolean, nullable=False, default=False)

    # Detección de Reciclaje / Duplicidad (ImageHash)
    es_duplicada = Column(Boolean, nullable=False, default=False)
    duplicada_con_evidencia_id = Column(Integer, nullable=True)     # evidencia_id con la que colisionó
    distancia_hamming = Column(Integer, nullable=True)

    # Análisis de Visión con IA (Semana 14)
    vision_analizada = Column(Boolean, nullable=False, default=False)
    vision_paquete = Column(Boolean, nullable=True)
    vision_fachada = Column(Boolean, nullable=True)
    vision_persona = Column(Boolean, nullable=True)
    vision_texto_sospechoso = Column(Boolean, nullable=True)
    vision_explicacion = Column(Text, nullable=True)
    vision_proveedor = Column(String(50), nullable=True)            # gemini, groq, openrouter, ollama

    # Semáforo final y resolución
    # verde: confiable | ambar: advertencia leve | rojo: alta sospecha de fraude / evidencia inválida
    semaforo = Column(String(20), nullable=False, default="verde", index=True)
    motivo_alerta = Column(Text, nullable=True)                     # Resumen de motivos que dispararon ámbar/rojo

    # Estado de gobernanza humana
    # PENDIENTE: no revisado | VALIDA: confirmada por admin | OBSERVADA: rechazada/observada por admin
    estado_revision = Column(String(20), nullable=False, default="PENDIENTE", index=True)

    creado_en = Column(DateTime, default=datetime.utcnow, index=True)
    actualizado_en = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relación con el historial de dictámenes humanos
    revisiones = relationship("RevisionHumana", back_populates="analisis", cascade="all, delete-orphan")
