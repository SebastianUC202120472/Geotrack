# app/models/parametro.py
# Tabla 'parametros_sistema' (CUS-06): catálogos administrables del sistema. Cada fila
# es un parámetro dentro de una categoría. Hoy se usa para los motivos de rechazo
# (categoria='motivo_rechazo', clave=el texto del motivo); el diseño deja lugar para
# otros catálogos a futuro (zonas, distritos, valores de configuración con valor_json).
from sqlalchemy import Column, Integer, String, JSON
from app.db.database import Base


class ParametroSistema(Base):
    __tablename__ = "parametros_sistema"

    id = Column(Integer, primary_key=True, index=True)
    categoria = Column(String(50), nullable=False, index=True)  # ej. 'motivo_rechazo'
    clave = Column(String(120), nullable=False)                 # ej. 'Cliente ausente'
    valor_json = Column(JSON, nullable=True)                    # valor estructurado opcional
