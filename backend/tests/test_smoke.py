# tests/test_smoke.py
# ============================================================================
# PRUEBAS DE HUMO ("smoke tests") — se ejecutan en GitHub Actions (Fase 4.3)
# ----------------------------------------------------------------------------
# ¿QUÉ HACE?  Verifica que el código de FastAPI "corre correctamente" sin
#             necesitar una base de datos:
#               - La app importa y se construye bien.
#               - Las rutas clave están registradas.
#               - La lógica pura (seguridad, VRP, validaciones) funciona.
# ¿POR QUÉ sin BD?  Estas pruebas validan el CÓDIGO, no la conexión. Por eso
#             NO arrancan el servidor (que sí pediría PostgreSQL). Importar la
#             app no abre conexión (el engine de SQLAlchemy es "perezoso").
# ============================================================================
from app.main import app
from app.core.security import get_password_hash, verify_password, create_access_token, decode_access_token
from app.services.router import optimizar_secuencia_pedidos
from app.schemas.ruta import ActualizarEstadoRequest


def _paths():
    """Devuelve el conjunto de rutas registradas en la app."""
    return {getattr(r, "path", "") for r in app.routes}


def test_la_app_se_construye():
    """La aplicación FastAPI se crea con el título correcto."""
    assert app.title == "SIOL-SAVA API"


def test_rutas_clave_registradas():
    """Las URLs principales de cada fase existen."""
    paths = _paths()
    assert "/api/auth/login" in paths                       # Fase 1
    # Fase 2 (Inbound): los pedidos entran al aceptar la solicitud de recojo (Excel) y
    # se agrupan por zona. (Reemplaza al antiguo "/api/pedidos/upload", ya retirado.)
    assert "/api/recojos/aceptar" in paths
    assert "/api/pedidos/zonas" in paths
    assert "/api/conductor/ruta-activa" in paths             # Fase 3
    assert "/api/dashboard/flota" in paths                   # Fase 4


def test_hash_de_contrasena():
    """Una contraseña encriptada se verifica bien y no se guarda en texto plano."""
    hash_ = get_password_hash("secreto123")
    assert hash_ != "secreto123"
    assert verify_password("secreto123", hash_) is True
    assert verify_password("incorrecta", hash_) is False


def test_token_jwt_ida_y_vuelta():
    """Un token creado se puede decodificar y conserva los datos (sub, rol)."""
    token = create_access_token({"sub": "admin@siol.com", "rol": "admin"})
    payload = decode_access_token(token)
    assert payload["sub"] == "admin@siol.com"
    assert payload["rol"] == "admin"


def test_vrp_ordena_por_cercania():
    """El optimizador (CUS-19) arranca por el pedido más cercano al origen."""
    class P:
        def __init__(self, id, lat, lng):
            self.id, self.latitud, self.longitud = id, lat, lng

    pedidos = [P(1, -12.10, -77.05), P(2, -12.00, -77.00), P(3, -12.05, -77.02)]
    orden = [p.id for p in optimizar_secuencia_pedidos(pedidos, -12.00, -77.00)]
    assert orden[0] == 2  # el más cercano al punto de partida


def test_validador_de_estado_de_entrega():
    """El estado se normaliza a mayúsculas y solo acepta ENTREGADO/FALLIDO."""
    assert ActualizarEstadoRequest(estado="entregado").estado == "ENTREGADO"
    try:
        ActualizarEstadoRequest(estado="OTRO")
        assert False, "debió rechazar un estado inválido"
    except Exception:
        assert True
