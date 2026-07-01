# Registra todos los modelos en Base.metadata para create_all y Alembic.
from .usuario import Usuario
from .cliente import ClienteCorporativo
from .vehiculo import Vehiculo
from .pedido import Pedido
from .ruta import Ruta, RutaDetalle
from .historial import HistorialPedido
from .correo import Conversacion, MensajeCorreo, MensajeAdjunto
from .conductor import PerfilConductor
from .reporte import Reporte
from .ubicacion import UbicacionConductor
from .liquidacion import Liquidacion
from .evidencia import EvidenciaEntrega
from .solicitud_restablecimiento import SolicitudRestablecimiento
from .parametro import ParametroSistema
from .incidencia import Incidencia
from .solicitud_recojo import SolicitudRecojo
from .notificacion import Notificacion
from .evidencia_recojo import EvidenciaRecojo
from .geocoding_cache import GeocodificacionCache
