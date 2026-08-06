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
from types import SimpleNamespace

from app.main import app
from app.core.security import get_password_hash, verify_password, create_access_token, decode_access_token
from app.services.router import optimizar_secuencia_pedidos
from app.services.ruta_service import separar_paradas_a_optimizar
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
    assert "/api/portal/pedidos/{codigo}/buscar" in paths      # Fase 2 portal
    assert "/api/reclamos/" in paths                         # Libro de Reclamaciones


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


def _parada(estado_entrega, pedido_id, lat=-12.05):
    """Arma una tupla (detalle, pedido) de prueba. Recibe estado de la parada, id y latitud."""
    return (
        SimpleNamespace(estado_entrega=estado_entrega),
        SimpleNamespace(id=pedido_id, latitud=lat, longitud=-77.03),
    )


def test_reoptimizar_no_toca_las_paradas_ya_gestionadas():
    """Reoptimizar a mitad de ruta no debe devolver a 'en camino' lo ya entregado."""
    detalles = [
        _parada("ENTREGADO", 1),
        _parada("FALLIDO", 2),
        _parada("PENDIENTE", 3),
        _parada("PENDIENTE", 4),
    ]
    hechas, pendientes = separar_paradas_a_optimizar(detalles)
    assert hechas == 2
    assert [p.id for p in pendientes] == [3, 4]


def test_optimizar_descarta_paradas_sin_coordenadas():
    """Un pedido sin geocodificar no entra en el calculo de la secuencia."""
    detalles = [_parada("PENDIENTE", 1, lat=None), _parada("PENDIENTE", 2)]
    hechas, pendientes = separar_paradas_a_optimizar(detalles)
    assert hechas == 0
    assert [p.id for p in pendientes] == [2]


def test_optimizar_sin_pendientes_no_devuelve_nada():
    """Con toda la ruta cerrada no queda nada que reordenar."""
    hechas, pendientes = separar_paradas_a_optimizar([_parada("ENTREGADO", 1)])
    assert hechas == 1
    assert pendientes == []


def test_validador_de_estado_de_entrega():
    """El estado se normaliza a mayúsculas y solo acepta ENTREGADO/FALLIDO."""
    assert ActualizarEstadoRequest(estado="entregado").estado == "ENTREGADO"
    try:
        ActualizarEstadoRequest(estado="OTRO")
        assert False, "debió rechazar un estado inválido"
    except Exception:
        assert True
