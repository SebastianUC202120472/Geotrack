# Pruebas del modulo de catalogo y capacidad (Idea 3).
# No necesitan PostgreSQL: usan SQLite en memoria y funciones puras.
from types import SimpleNamespace

import pytest
from fastapi import FastAPI, HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.deps import get_current_admin, get_current_user
from app.api.modulo_capacidad import router as capacidad_router
from app.core.config import settings
from app.db.database import Base
from app.main import app
from app.models.capacidad import (
    AuditoriaCapacidad,
    ConfiguracionCapacidad,
    ModeloPersonalizado,
    VinculacionPlaca,
)
from app.schemas.capacidad import (
    CalculoRequest,
    ConfiguracionUpdateRequest,
    ModeloCreateRequest,
    ModeloUpdateRequest,
    VinculacionPlacaRequest,
)
from app.services import capacidad_service

TABLAS = [
    VinculacionPlaca.__table__,
    ModeloPersonalizado.__table__,
    ConfiguracionCapacidad.__table__,
    AuditoriaCapacidad.__table__,
]


@pytest.fixture()
def db():
    """Sesion SQLite en memoria con solo las tablas del modulo."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine, tables=TABLAS)
    sesion = sessionmaker(bind=engine)()
    try:
        yield sesion
    finally:
        sesion.close()


def _vehiculo(placa="ABC-123"):
    """Vehiculo de prueba con los campos que usa el servicio."""
    return SimpleNamespace(
        id=1,
        placa=placa,
        marca="Toyota",
        capacidad_volumetrica=5.0,
        capacidad_cajas=20,
        estado="DISPONIBLE",
        conductor_id=None,
        eliminado_en=None,
    )


def _parchear_flota(monkeypatch, vehiculo=None):
    """Evita consultar las tablas del nucleo en las pruebas de vinculacion."""
    vehiculo = vehiculo or _vehiculo()
    monkeypatch.setattr(
        capacidad_service.vehiculo_repository,
        "obtener_por_placa",
        lambda db, placa: vehiculo if placa == vehiculo.placa else None,
    )
    monkeypatch.setattr(
        capacidad_service.vehiculo_repository, "listar", lambda db: [vehiculo]
    )
    monkeypatch.setattr(capacidad_service, "_nombre_conductor", lambda db, v: None)


def _plan(items, vehiculos, factor=0.85, paradas=25, viajes=3):
    """Atajo para calcular un plan en las pruebas."""
    return capacidad_service.calcular_plan(
        items, vehiculos, factor, paradas, viajes, 60
    )


def _camion(placa="T-01", volumen=7.5, carga=2000.0):
    """Vehiculo planificable de prueba."""
    return {
        "placa": placa,
        "modelo_id": "demo-camion",
        "marca": "Demo",
        "modelo": "Camion",
        "tipo": "camion_ligero",
        "volumen_m3": volumen,
        "carga_kg": carga,
    }


# ---------------------------------------------------------------------------
# Catalogo
# ---------------------------------------------------------------------------


def test_catalogo_tiene_al_menos_79_modelos():
    """La ficha pide 60 modelos y marcas nuevas: se entregan 79."""
    assert len(capacidad_service.leer_catalogo_base().modelos) >= 79


def test_catalogo_ids_unicos():
    """Ningun modelo repite id."""
    ids = [m.id for m in capacidad_service.leer_catalogo_base().modelos]
    assert len(ids) == len(set(ids))


def test_catalogo_incluye_marcas_pedidas():
    """Jetour, DFSK y Changan estan en el catalogo."""
    marcas = {m.marca for m in capacidad_service.leer_catalogo_base().modelos}
    assert {"Jetour", "DFSK", "Changan"}.issubset(marcas)


def test_catalogo_incluye_tipos_pedidos():
    """Sedan, hatchback, SUV y van existen ademas de los camiones."""
    tipos = {m.tipo.value for m in capacidad_service.leer_catalogo_base().modelos}
    assert {"sedan", "hatchback", "suv", "van"}.issubset(tipos)


def test_todos_los_modelos_tienen_fuente():
    """Cada modelo declara texto de fuente y URL."""
    for modelo in capacidad_service.leer_catalogo_base().modelos:
        assert modelo.fuente
        assert modelo.fuente_url


def test_catalogo_tiene_modelos_verificados():
    """Los 60 modelos originales quedan marcados como verificados."""
    verificados = [m for m in capacidad_service.leer_catalogo_base().modelos if m.verificado]
    assert len(verificados) >= 60


def test_filtro_por_busqueda_marca_y_tipo():
    """Los filtros del catalogo funcionan sin tocar la base."""
    modelos = capacidad_service.leer_catalogo_base().modelos
    assert capacidad_service.filtrar_catalogo(modelos, busqueda="jetour")
    assert capacidad_service.filtrar_catalogo(modelos, marca="DFSK")
    solo_suv = capacidad_service.filtrar_catalogo(modelos, tipo="suv")
    assert solo_suv and all(m.tipo.value == "suv" for m in solo_suv)


def test_placa_formato_valido():
    """La placa peruana ABC-123 se acepta y se normaliza."""
    datos = VinculacionPlacaRequest(placa="abc-123", modelo_id="toyota-hilux-2024")
    assert datos.placa == "ABC-123"


def test_placa_formato_invalido():
    """Una placa con formato incorrecto se rechaza."""
    with pytest.raises(ValidationError):
        VinculacionPlacaRequest(placa="ABC123", modelo_id="toyota-hilux-2024")


# ---------------------------------------------------------------------------
# Vinculaciones persistentes
# ---------------------------------------------------------------------------


def test_vincular_persiste_y_aparece_en_historial(db, monkeypatch):
    """Vincular guarda de verdad y el historial lo devuelve."""
    _parchear_flota(monkeypatch)

    fila = capacidad_service.vincular(
        db,
        VinculacionPlacaRequest(placa="ABC-123", modelo_id="toyota-hilux-2024"),
        "admin@siol.com",
    )
    assert fila.id is not None

    historial = capacidad_service.listar_vinculaciones(db)
    assert len(historial) == 1
    assert historial[0]["placa"] == "ABC-123"
    assert historial[0]["marca"] == "Toyota"
    assert historial[0]["vehiculo_encontrado"] is True


def test_vincular_placa_duplicada_da_409(db, monkeypatch):
    """Una placa no puede tener dos modelos."""
    _parchear_flota(monkeypatch)
    datos = VinculacionPlacaRequest(placa="ABC-123", modelo_id="toyota-hilux-2024")
    capacidad_service.vincular(db, datos, "admin@siol.com")

    with pytest.raises(HTTPException) as error:
        capacidad_service.vincular(db, datos, "admin@siol.com")
    assert error.value.status_code == 409


def test_vincular_placa_inexistente_da_404(db, monkeypatch):
    """Solo se vinculan placas registradas en la flota."""
    monkeypatch.setattr(
        capacidad_service.vehiculo_repository, "obtener_por_placa", lambda db, p: None
    )
    with pytest.raises(HTTPException) as error:
        capacidad_service.vincular(
            db,
            VinculacionPlacaRequest(placa="ZZZ-999", modelo_id="toyota-hilux-2024"),
            "admin@siol.com",
        )
    assert error.value.status_code == 404


def test_vincular_modelo_inexistente_da_404(db, monkeypatch):
    """No se puede vincular un modelo que no esta en el catalogo."""
    _parchear_flota(monkeypatch)
    with pytest.raises(HTTPException) as error:
        capacidad_service.vincular(
            db,
            VinculacionPlacaRequest(placa="ABC-123", modelo_id="no-existe-2025"),
            "admin@siol.com",
        )
    assert error.value.status_code == 404


def test_desvincular_borra_el_registro(db, monkeypatch):
    """Al quitar la vinculacion el historial queda vacio."""
    _parchear_flota(monkeypatch)
    fila = capacidad_service.vincular(
        db,
        VinculacionPlacaRequest(placa="ABC-123", modelo_id="toyota-hilux-2024"),
        "admin@siol.com",
    )
    capacidad_service.eliminar_vinculacion(db, fila.id, "admin@siol.com")
    assert capacidad_service.listar_vinculaciones(db) == []


# ---------------------------------------------------------------------------
# Altas y ediciones del catalogo
# ---------------------------------------------------------------------------


def _nuevo_modelo():
    """Datos validos para crear un modelo propio."""
    return ModeloCreateRequest(
        marca="Marca X",
        modelo="Demo Van",
        tipo="van",
        largo_m=2.0,
        ancho_m=1.5,
        alto_m=1.2,
        volumen_util_m3=3.6,
        carga_util_kg=900,
        fuente="Ficha de prueba",
        fuente_url="https://example.com/ficha",
    )


def test_crear_modelo_personalizado(db):
    """Un modelo nuevo se guarda y se puede consultar."""
    modelo = capacidad_service.crear_modelo(db, _nuevo_modelo(), "admin@siol.com")
    assert modelo.id == "marca-x-demo-van"
    assert modelo.es_personalizado is True
    assert capacidad_service.obtener_modelo(db, modelo.id).carga_util_kg == 900


def test_crear_modelo_duplicado_da_409(db):
    """No se repiten ids de modelo."""
    capacidad_service.crear_modelo(db, _nuevo_modelo(), "admin@siol.com")
    with pytest.raises(HTTPException) as error:
        capacidad_service.crear_modelo(db, _nuevo_modelo(), "admin@siol.com")
    assert error.value.status_code == 409


def test_editar_modelo_base_guarda_copia(db):
    """Editar un modelo del JSON base crea una fila propia sin tocar el JSON."""
    actualizado = capacidad_service.actualizar_modelo(
        db,
        "toyota-hilux-2024",
        ModeloUpdateRequest(carga_util_kg=1100),
        "admin@siol.com",
    )
    assert actualizado.carga_util_kg == 1100
    leido = capacidad_service.obtener_modelo(db, "toyota-hilux-2024")
    assert leido.carga_util_kg == 1100
    assert leido.es_personalizado is True


def test_no_se_borra_un_modelo_base(db):
    """Los modelos del JSON base solo se editan, no se borran."""
    with pytest.raises(HTTPException) as error:
        capacidad_service.eliminar_modelo(db, "toyota-hilux-2024", "admin@siol.com")
    assert error.value.status_code == 409


def test_borrar_modelo_propio(db):
    """Un modelo creado desde el panel si se puede borrar."""
    modelo = capacidad_service.crear_modelo(db, _nuevo_modelo(), "admin@siol.com")
    capacidad_service.eliminar_modelo(db, modelo.id, "admin@siol.com")
    assert capacidad_service.obtener_modelo(db, modelo.id) is None


# ---------------------------------------------------------------------------
# Configuracion
# ---------------------------------------------------------------------------


def test_configuracion_por_defecto(db):
    """La configuracion nace con factor 0.85 y topes razonables."""
    config = capacidad_service.obtener_configuracion(db)
    assert config.factor_aprovechamiento == 0.85
    assert config.max_paradas_por_viaje == 25


def test_actualizar_configuracion(db):
    """Los parametros se guardan y quedan auditados."""
    config = capacidad_service.actualizar_configuracion(
        db,
        ConfiguracionUpdateRequest(factor_aprovechamiento=0.7, max_viajes_por_dia=2),
        "admin@siol.com",
    )
    assert config.factor_aprovechamiento == 0.7
    assert config.max_viajes_por_dia == 2
    assert capacidad_service.historial_auditoria(db)[0]["accion"] == "editar"


# ---------------------------------------------------------------------------
# Calculadora
# ---------------------------------------------------------------------------


def test_calculo_manual_sml():
    """Las cajas S/M/L se reparten entre viajes sin perder ninguna."""
    items = capacidad_service.items_desde_cantidades({"S": 10, "M": 5, "L": 2})
    plan = _plan(items, [_camion()], factor=1.0, paradas=100)

    assert plan["resumen"]["total_pedidos"] == 17
    assert sum(v["paradas"] for v in plan["viajes"]) == 17
    assert plan["resumen"]["pedidos_sin_asignar"] == 0


def test_factor_de_aprovechamiento_reduce_capacidad():
    """Con factor 0.5 hacen falta mas viajes que con 1.0."""
    items = capacidad_service.items_demo(120)
    plan_completo = _plan(items, [_camion()], factor=1.0, paradas=100)
    plan_mitad = _plan(items, [_camion()], factor=0.5, paradas=100)
    assert (
        plan_mitad["resumen"]["viajes_necesarios"]
        >= plan_completo["resumen"]["viajes_necesarios"]
    )
    for viaje in plan_mitad["viajes"]:
        assert viaje["volumen_m3"] <= viaje["capacidad_m3"] + 0.001


def test_pedidos_reales_usan_su_peso_y_volumen():
    """Si el pedido trae medidas, no se estiman."""
    pedidos = [
        SimpleNamespace(
            id=1, codigo="PD-001", distrito="Lima", peso_kg=80.0, volumen_m3=0.8
        )
    ]
    items = capacidad_service.items_desde_pedidos(pedidos)
    assert items[0]["estimado"] is False
    assert items[0]["peso_kg"] == 80.0
    assert items[0]["volumen_m3"] == 0.8


def test_pedidos_sin_medidas_se_marcan_estimados():
    """Sin peso/volumen se usa S/M/L y queda marcado como estimado."""
    pedidos = [
        SimpleNamespace(id=4, codigo="PD-004", distrito=None, peso_kg=None, volumen_m3=0)
    ]
    items = capacidad_service.items_desde_pedidos(pedidos)
    assert items[0]["estimado"] is True
    assert items[0]["tamano_estimado"] in ("S", "M", "L")
    assert items[0]["peso_kg"] > 0


def test_plan_avisa_cuando_un_pedido_no_cabe():
    """Un pedido mas grande que el vehiculo queda sin asignar y alerta."""
    items = capacidad_service.items_desde_cantidades({"L": 1})
    items[0]["volumen_m3"] = 100
    plan = _plan(items, [_camion()])
    assert plan["resumen"]["pedidos_sin_asignar"] == 1
    assert any(a["codigo"] == "capacidad_insuficiente" for a in plan["alertas"])


def test_plan_alerta_cuando_supera_el_tope_de_paradas_por_viaje():
    """El tope de paradas es una alerta, no un limite que descarte carga."""
    plan = _plan(capacidad_service.items_demo(100), [_camion()], paradas=10)
    assert any(v["paradas"] > 10 for v in plan["viajes"])
    assert any(a["codigo"] == "tope_paradas_viaje" for a in plan["alertas"])


def test_caso_700_pedidos():
    """El caso de la semana 11: 700 pedidos caben en 6 vehiculos y 2 viajes."""
    vehiculos = [_camion(f"T-{i:02d}") for i in range(1, 7)]
    plan = _plan(capacidad_service.items_demo(700), vehiculos, paradas=60, viajes=2)

    resumen = plan["resumen"]
    assert resumen["total_pedidos"] == 700
    assert resumen["pedidos_sin_asignar"] == 0
    assert resumen["viajes_necesarios"] <= 12
    assert resumen["vehiculos_necesarios"] <= 6
    asignados = sum(v["paradas"] for v in plan["viajes"])
    assert asignados == 700


def test_caso_700_con_tope_de_25_paradas_alerta():
    """Con 25 paradas por viaje el plan avisa que la jornada se excede."""
    vehiculos = [_camion(f"T-{i:02d}") for i in range(1, 7)]
    plan = _plan(capacidad_service.items_demo(700), vehiculos, paradas=25, viajes=3)

    assert plan["resumen"]["pedidos_sin_asignar"] == 0
    assert any(a["codigo"] == "tope_paradas_viaje" for a in plan["alertas"])
    assert any(a["codigo"] == "jornada_excedida" for a in plan["alertas"])


def test_calculo_exige_vehiculo():
    """La peticion de calculo exige modelo_id o placa."""
    with pytest.raises(ValidationError):
        CalculoRequest(cantidades={"S": 1})


def test_calculo_exige_origen_de_carga():
    """La peticion de calculo exige cajas, pedidos o demo."""
    with pytest.raises(ValidationError):
        CalculoRequest(modelo_id="toyota-hilux-2024")


def test_calculo_rechaza_tamano_desconocido():
    """Solo se aceptan las tallas S, M y L."""
    with pytest.raises(ValidationError):
        CalculoRequest(modelo_id="toyota-hilux-2024", cantidades={"XL": 2})


def test_calculo_limita_el_factor():
    """El factor de aprovechamiento debe estar entre 0.5 y 1.0."""
    with pytest.raises(ValidationError):
        CalculoRequest(
            modelo_id="toyota-hilux-2024",
            cantidades={"S": 1},
            factor_aprovechamiento=1.5,
        )


def test_calculo_limita_la_cantidad_de_pedidos():
    """La demo no admite mas de 5000 pedidos."""
    with pytest.raises(ValidationError):
        CalculoRequest(modelo_id="toyota-hilux-2024", demo_pedidos=5001)


# ---------------------------------------------------------------------------
# Seguridad y registro de rutas
# ---------------------------------------------------------------------------


def _ruta(path, metodo):
    """Busca una ruta registrada por path y metodo HTTP."""
    for ruta in app.routes:
        if getattr(ruta, "path", None) == path and metodo in getattr(
            ruta, "methods", set()
        ):
            return ruta
    return None


def test_rutas_del_modulo_registradas():
    """Las rutas nuevas existen con el prefijo del modulo."""
    assert _ruta("/api/modulo-capacidad/catalogo", "GET")
    assert _ruta("/api/modulo-capacidad/vinculaciones", "GET")
    assert _ruta("/api/modulo-capacidad/vinculaciones", "POST")
    assert _ruta("/api/modulo-capacidad/calcular", "POST")
    assert _ruta("/api/modulo-capacidad/planificacion", "GET")


def test_endpoints_exigen_autenticacion():
    """Ningun endpoint del modulo queda publico."""
    rutas = [
        ("/api/modulo-capacidad/catalogo", "GET"),
        ("/api/modulo-capacidad/vinculaciones", "GET"),
        ("/api/modulo-capacidad/vinculaciones", "POST"),
        ("/api/modulo-capacidad/calcular", "POST"),
        ("/api/modulo-capacidad/planificacion", "GET"),
        ("/api/modulo-capacidad/configuracion", "PUT"),
        ("/api/modulo-capacidad/flota", "GET"),
    ]
    for path, metodo in rutas:
        ruta = _ruta(path, metodo)
        assert ruta is not None, f"Falta {metodo} {path}"
        assert ruta.dependant.dependencies, f"{metodo} {path} no pide autenticacion"


def test_almacen_no_puede_escribir():
    """El rol almacen recibe 403 al intentar una operacion de admin."""
    with pytest.raises(HTTPException) as error:
        get_current_admin(SimpleNamespace(rol="almacen", correo="almacen@siol.com"))
    assert error.value.status_code == 403


def test_token_invalido_da_401(db):
    """Un token invalido no permite entrar."""
    with pytest.raises(HTTPException) as error:
        get_current_user(token="no-es-un-jwt", db=db)
    assert error.value.status_code == 401


def test_flag_apagado_no_registra_rutas(monkeypatch):
    """Con MODULO_CAPACIDAD_ENABLED=false el modulo desaparece."""
    monkeypatch.setattr(settings, "MODULO_CAPACIDAD_ENABLED", False)
    app_prueba = FastAPI()
    assert capacidad_router.incluir_router(app_prueba) is False
    assert not any(
        getattr(r, "path", "").startswith("/api/modulo-capacidad")
        for r in app_prueba.routes
    )


def test_flag_encendido_registra_rutas(monkeypatch):
    """Con la bandera encendida el modulo se registra."""
    monkeypatch.setattr(settings, "MODULO_CAPACIDAD_ENABLED", True)
    app_prueba = FastAPI()
    assert capacidad_router.incluir_router(app_prueba) is True
    assert any(
        getattr(r, "path", "") == "/api/modulo-capacidad/salud"
        for r in app_prueba.routes
    )