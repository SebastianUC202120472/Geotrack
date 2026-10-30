
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
        lambda db, placa: (
            vehiculo if placa == vehiculo.placa else None
        ),
    )

    monkeypatch.setattr(
        capacidad_service.vehiculo_repository,
        "listar",
        lambda db: [vehiculo],
    )

    monkeypatch.setattr(
        capacidad_service,
        "_nombre_conductor",
        lambda db, v: None,
    )


def _plan(
    items,
    vehiculos,
    factor=0.85,
    paradas=25,
    viajes=3,
):
    """Atajo para calcular un plan en las pruebas."""

    return capacidad_service.calcular_plan(
        items,
        vehiculos,
        factor,
        paradas,
        viajes,
        60,
    )


def _camion(
    placa="T-01",
    volumen=7.5,
    carga=2000.0,
):
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


# ============================================================
# 1. CATALOGO
# ============================================================

def test_catalogo_tiene_al_menos_79_modelos():
    """La ficha pide 60 modelos y marcas nuevas: se entregan 79."""

    assert (
        len(capacidad_service.leer_catalogo_base().modelos)
        >= 79
    )


def test_catalogo_ids_unicos():
    """Ningun modelo repite id."""

    ids = [
        m.id
        for m in capacidad_service.leer_catalogo_base().modelos
    ]

    assert len(ids) == len(set(ids))


def test_catalogo_incluye_marcas_pedidas():
    """Jetour, DFSK y Changan estan en el catalogo."""

    marcas = {
        m.marca
        for m in capacidad_service.leer_catalogo_base().modelos
    }

    assert {
        "Jetour",
        "DFSK",
        "Changan",
    }.issubset(marcas)


def test_catalogo_incluye_tipos_pedidos():
    """Sedan, hatchback, SUV y van existen ademas de los camiones."""

    tipos = {
        m.tipo.value
        for m in capacidad_service.leer_catalogo_base().modelos
    }

    assert {
        "sedan",
        "hatchback",
        "suv",
        "van",
    }.issubset(tipos)


def test_todos_los_modelos_tienen_fuente():
    """Cada modelo declara texto de fuente y URL."""

    for modelo in capacidad_service.leer_catalogo_base().modelos:
        assert modelo.fuente
        assert modelo.fuente_url


def test_catalogo_tiene_modelos_verificados():
    """Los 60 modelos originales quedan marcados como verificados."""

    verificados = [
        m
        for m in capacidad_service.leer_catalogo_base().modelos
        if m.verificado
    ]

    assert len(verificados) >= 60


def test_filtro_por_busqueda_marca_y_tipo():
    """Los filtros del catalogo funcionan sin tocar la base."""

    modelos = capacidad_service.leer_catalogo_base().modelos

    assert capacidad_service.filtrar_catalogo(
        modelos,
        busqueda="jetour",
    )

    assert capacidad_service.filtrar_catalogo(
        modelos,
        marca="DFSK",
    )

    solo_suv = capacidad_service.filtrar_catalogo(
        modelos,
        tipo="suv",
    )

    assert solo_suv

    assert all(
        m.tipo.value == "suv"
        for m in solo_suv
    )


def test_placa_formato_valido():
    """La placa peruana ABC-123 se acepta y se normaliza."""

    datos = VinculacionPlacaRequest(
        placa="abc-123",
        modelo_id="toyota-hilux-2024",
    )

    assert datos.placa == "ABC-123"


def test_placa_formato_invalido():
    """Una placa con formato incorrecto se rechaza."""

    with pytest.raises(ValidationError):
        VinculacionPlacaRequest(
            placa="ABC123",
            modelo_id="toyota-hilux-2024",
        )


# ============================================================
# 2. VINCULACIONES PERSISTENTES
# ============================================================

def test_vincular_persiste_y_aparece_en_historial(
    db,
    monkeypatch,
):
    """Vincular guarda de verdad y el historial lo devuelve."""

    _parchear_flota(monkeypatch)

    fila = capacidad_service.vincular(
        db,
        VinculacionPlacaRequest(
            placa="ABC-123",
            modelo_id="toyota-hilux-2024",
        ),
        "admin@siol.com",
    )

    assert fila.id is not None

    historial = capacidad_service.listar_vinculaciones(db)

    assert len(historial) == 1
    assert historial[0]["placa"] == "ABC-123"
    assert historial[0]["marca"] == "Toyota"
    assert historial[0]["vehiculo_encontrado"] is True


def test_vincular_placa_duplicada_da_409(
    db,
    monkeypatch,
):
    """Una placa no puede tener dos modelos."""

    _parchear_flota(monkeypatch)

    datos = VinculacionPlacaRequest(
        placa="ABC-123",
        modelo_id="toyota-hilux-2024",
    )

    capacidad_service.vincular(
        db,
        datos,
        "admin@siol.com",
    )

    with pytest.raises(HTTPException) as error:
        capacidad_service.vincular(
            db,
            datos,
            "admin@siol.com",
        )

    assert error.value.status_code == 409


def test_vincular_placa_inexistente_da_404(
    db,
    monkeypatch,
):
    """Solo se vinculan placas registradas en la flota."""

    monkeypatch.setattr(
        capacidad_service.vehiculo_repository,
        "obtener_por_placa",
        lambda db, p: None,
    )

    with pytest.raises(HTTPException) as error:
        capacidad_service.vincular(
            db,
            VinculacionPlacaRequest(
                placa="ZZZ-999",
                modelo_id="toyota-hilux-2024",
            ),
            "admin@siol.com",
        )

    assert error.value.status_code == 404


def test_vincular_modelo_inexistente_da_404(
    db,
    monkeypatch,
):
    """No se puede vincular un modelo que no esta en el catalogo."""

    _parchear_flota(monkeypatch)

    with pytest.raises(HTTPException) as error:
        capacidad_service.vincular(
            db,
            VinculacionPlacaRequest(
                placa="ABC-123",
                modelo_id="no-existe-2025",
            ),
            "admin@siol.com",
        )

    assert error.value.status_code == 404


def test_desvincular_borra_el_registro(
    db,
    monkeypatch,
):
    """Al quitar la vinculacion el historial queda vacio."""

    _parchear_flota(monkeypatch)

    fila = capacidad_service.vincular(
        db,
        VinculacionPlacaRequest(
            placa="ABC-123",
            modelo_id="toyota-hilux-2024",
        ),
        "admin@siol.com",
    )

    capacidad_service.eliminar_vinculacion(
        db,
        fila.id,
        "admin@siol.com",
    )

    assert capacidad_service.listar_vinculaciones(db) == []


# ============================================================
# 3. ALTAS Y EDICIONES DEL CATALOGO
# ============================================================

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

    modelo = capacidad_service.crear_modelo(
        db,
        _nuevo_modelo(),
        "admin@siol.com",
    )

    assert modelo.id == "marca-x-demo-van"
    assert modelo.es_personalizado is True

    assert (
        capacidad_service.obtener_modelo(
            db,
            modelo.id,
        ).carga_util_kg
        == 900
    )


def test_crear_modelo_duplicado_da_409(db):
    """No se repiten ids de modelo."""

    capacidad_service.crear_modelo(
        db,
        _nuevo_modelo(),
        "admin@siol.com",
    )

    with pytest.raises(HTTPException) as error:
        capacidad_service.crear_modelo(
            db,
            _nuevo_modelo(),
            "admin@siol.com",
        )

    assert error.value.status_code == 409


def test_editar_modelo_base_guarda_copia(db):
    """Editar un modelo del JSON crea una fila propia."""

    actualizado = capacidad_service.actualizar_modelo(
        db,
        "toyota-hilux-2024",
        ModeloUpdateRequest(
            carga_util_kg=1100,
        ),
        "admin@siol.com",
    )

    assert actualizado.carga_util_kg == 1100

    leido = capacidad_service.obtener_modelo(
        db,
        "toyota-hilux-2024",
    )

    assert leido.carga_util_kg == 1100
    assert leido.es_personalizado is True


def test_no_se_borra_un_modelo_base(db):
    """Los modelos del JSON base solo se editan, no se borran."""

    with pytest.raises(HTTPException) as error:
        capacidad_service.eliminar_modelo(
            db,
            "toyota-hilux-2024",
            "admin@siol.com",
        )

    assert error.value.status_code == 409


def test_borrar_modelo_propio(db):
    """Un modelo creado desde el panel si se puede borrar."""

    modelo = capacidad_service.crear_modelo(
        db,
        _nuevo_modelo(),
        "admin@siol.com",
    )

    capacidad_service.eliminar_modelo(
        db,
        modelo.id,
        "admin@siol.com",
    )

    assert (
        capacidad_service.obtener_modelo(
            db,
            modelo.id,
        )
        is None
    )


# ============================================================
# 4. CONFIGURACION
# ============================================================

def test_configuracion_por_defecto(db):
    """Comprueba los valores iniciales."""

    config = capacidad_service.obtener_configuracion(db)

    assert config.factor_aprovechamiento == 0.85
    assert config.max_paradas_por_viaje == 25


def test_actualizar_configuracion(db):
    """Los parametros se guardan y quedan auditados."""

    config = capacidad_service.actualizar_configuracion(
        db,
        ConfiguracionUpdateRequest(
            factor_aprovechamiento=0.7,
            max_viajes_por_dia=2,
        ),
        "admin@siol.com",
    )

    assert config.factor_aprovechamiento == 0.7
    assert config.max_viajes_por_dia == 2

    assert (
        capacidad_service.historial_auditoria(db)[0]["accion"]
        == "editar"
    )


# ============================================================
# 5. CALCULADORA DE CAPACIDAD
# ============================================================

def test_calculo_manual_sml():
    """Las cajas S/M/L se reparten sin perder ninguna."""

    items = capacidad_service.items_desde_cantidades({
        "S": 10,
        "M": 5,
        "L": 2,
    })

    plan = _plan(
        items,
        [_camion()],
        factor=1.0,
        paradas=100,
    )

    assert plan["resumen"]["total_pedidos"] == 17

    assert (
        sum(v["paradas"] for v in plan["viajes"])
        == 17
    )

    assert (
        plan["resumen"]["pedidos_sin_asignar"]
        == 0
    )


def test_factor_de_aprovechamiento_reduce_capacidad():
    """Con factor 0.5 hacen falta mas viajes que con 1.0."""

    items = capacidad_service.items_demo(120)

    plan_completo = _plan(
        items,
        [_camion()],
        factor=1.0,
        paradas=100,
    )

    plan_mitad = _plan(
        items,
        [_camion()],
        factor=0.5,
        paradas=100,
    )

    assert (
        plan_mitad["resumen"]["viajes_necesarios"]
        >= plan_completo["resumen"]["viajes_necesarios"]
    )

    for viaje in plan_mitad["viajes"]:
        assert (
            viaje["volumen_m3"]
            <= viaje["capacidad_m3"] + 0.001
        )


def test_pedidos_reales_usan_su_peso_y_volumen():
    """Si el pedido trae medidas, no se estiman."""

    pedidos = [
        SimpleNamespace(
            id=1,
            codigo="PD-001",
            distrito="Lima",
            peso_kg=80.0,
            volumen_m3=0.8,
        )
    ]

    items = capacidad_service.items_desde_pedidos(pedidos)

    assert items[0]["estimado"] is False
    assert items[0]["peso_kg"] == 80.0
    assert items[0]["volumen_m3"] == 0.8


def test_pedidos_sin_medidas_se_marcan_estimados():
    """Sin peso o volumen se usa S/M/L estimado."""

    pedidos = [
        SimpleNamespace(
            id=4,
            codigo="PD-004",
            distrito=None,
            peso_kg=None,
            volumen_m3=0,
        )
    ]

    items = capacidad_service.items_desde_pedidos(pedidos)

    assert items[0]["estimado"] is True

    assert items[0]["tamano_estimado"] in (
        "S",
        "M",
        "L",
    )

    assert items[0]["peso_kg"] > 0


def test_plan_avisa_cuando_un_pedido_no_cabe():
    """Un pedido grande queda pendiente y genera alerta."""

    items = capacidad_service.items_desde_cantidades({
        "L": 1,
    })

    items[0]["volumen_m3"] = 100

    plan = _plan(
        items,
        [_camion()],
    )

    assert plan["resumen"]["pedidos_sin_asignar"] == 1

    assert any(
        a["codigo"] == "capacidad_insuficiente"
        for a in plan["alertas"]
    )


def test_plan_alerta_cuando_supera_el_tope_de_paradas_por_viaje():
    """El limite de paradas se respeta."""

    plan = _plan(
        capacidad_service.items_demo(100),
        [_camion()],
        paradas=10,
    )

    assert all(
        v["paradas"] <= 10
        for v in plan["viajes"]
    )

    assert (
        sum(v["paradas"] for v in plan["viajes"])
        + plan["resumen"]["pedidos_sin_asignar"]
        == 100
    )

    assert any(
        a["codigo"] == "capacidad_insuficiente"
        for a in plan["alertas"]
    )


# ============================================================
# 6. PLANIFICACION CON 700 PEDIDOS
# ============================================================

def test_caso_700_pedidos():
    """Con seis vehiculos se informa lo pendiente."""

    vehiculos = [
        _camion(f"T-{i:02d}")
        for i in range(1, 7)
    ]

    plan = _plan(
        capacidad_service.items_demo(700),
        vehiculos,
        paradas=60,
        viajes=2,
    )

    asignados = sum(
        v["paradas"]
        for v in plan["viajes"]
    )

    assert plan["resumen"]["total_pedidos"] == 700
    assert asignados <= 360

    assert (
        asignados
        + plan["resumen"]["pedidos_sin_asignar"]
        == 700
    )

    assert all(
        v["paradas"] <= 60
        for v in plan["vehiculos"]
    )


def test_caso_700_con_tope_de_25_paradas_alerta():
    """Ningun viaje supera 25 paradas ni 60 por jornada."""

    vehiculos = [
        _camion(f"T-{i:02d}")
        for i in range(1, 7)
    ]

    plan = _plan(
        capacidad_service.items_demo(700),
        vehiculos,
        paradas=25,
        viajes=3,
    )

    assert all(
        v["paradas"] <= 25
        for v in plan["viajes"]
    )

    assert all(
        v["paradas"] <= 60
        and v["viajes"] <= 3
        for v in plan["vehiculos"]
    )

    assert (
        sum(v["paradas"] for v in plan["viajes"])
        + plan["resumen"]["pedidos_sin_asignar"]
        == 700
    )


# ============================================================
# 7. VALIDACIONES DE SOLICITUDES
# ============================================================

def test_calculo_exige_vehiculo():
    """El calculo exige modelo_id o placa."""

    with pytest.raises(ValidationError):
        CalculoRequest(
            cantidades={"S": 1},
        )


def test_calculo_exige_origen_de_carga():
    """La peticion exige cajas, pedidos o demo."""

    with pytest.raises(ValidationError):
        CalculoRequest(
            modelo_id="toyota-hilux-2024",
        )


def test_calculo_rechaza_tamano_desconocido():
    """Solo se aceptan tallas S, M y L."""

    with pytest.raises(ValidationError):
        CalculoRequest(
            modelo_id="toyota-hilux-2024",
            cantidades={"XL": 2},
        )


def test_calculo_limita_el_factor():
    """El factor debe estar entre 0.5 y 1.0."""

    with pytest.raises(ValidationError):
        CalculoRequest(
            modelo_id="toyota-hilux-2024",
            cantidades={"S": 1},
            factor_aprovechamiento=1.5,
        )


def test_calculo_limita_la_cantidad_de_pedidos():
    """La demo no admite mas de 5000 pedidos."""

    with pytest.raises(ValidationError):
        CalculoRequest(
            modelo_id="toyota-hilux-2024",
            demo_pedidos=5001,
        )


# ============================================================
# 8. SEGURIDAD Y REGISTRO DE RUTAS
# ============================================================


def _ruta(path, metodo):
    """Busca una ruta registrada, compatible con FastAPI nuevo y antiguo."""

    # Comprueba que el endpoint exista en la aplicacion principal.
    rutas_openapi = app.openapi().get("paths", {})

    if metodo.lower() not in rutas_openapi.get(path, {}):
        return None

    # Recupera la ruta original para verificar sus dependencias.
    prefijo = "/api/modulo-capacidad"

    if not path.startswith(prefijo + "/"):
        return None

    ruta_relativa = path[len(prefijo):]

    for ruta in capacidad_router.router.routes:
        if (
            getattr(ruta, "path", None) == ruta_relativa
            and metodo in getattr(ruta, "methods", set())
        ):
            return ruta

    return None



def test_rutas_del_modulo_registradas():
    """Comprueba los endpoints principales."""

    assert _ruta(
        "/api/modulo-capacidad/catalogo",
        "GET",
    )

    assert _ruta(
        "/api/modulo-capacidad/vinculaciones",
        "GET",
    )

    assert _ruta(
        "/api/modulo-capacidad/vinculaciones",
        "POST",
    )

    assert _ruta(
        "/api/modulo-capacidad/calcular",
        "POST",
    )

    assert _ruta(
        "/api/modulo-capacidad/planificacion",
        "GET",
    )


def test_endpoints_exigen_autenticacion():
    """Comprueba dependencias de autenticacion."""

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

        assert ruta is not None, (
            f"Falta {metodo} {path}"
        )

        assert ruta.dependant.dependencies, (
            f"{metodo} {path} no pide autenticacion"
        )


def test_almacen_no_puede_escribir():
    """El rol almacen no posee acceso administrativo."""

    with pytest.raises(HTTPException) as error:
        get_current_admin(
            SimpleNamespace(
                rol="almacen",
                correo="almacen@siol.com",
            )
        )

    assert error.value.status_code == 403


def test_token_invalido_da_401(db):
    """Un token invalido no permite entrar."""

    with pytest.raises(HTTPException) as error:
        get_current_user(
            token="no-es-un-jwt",
            db=db,
        )

    assert error.value.status_code == 401


def test_flag_apagado_no_registra_rutas(monkeypatch):
    """El modulo puede desactivarse por configuracion."""

    monkeypatch.setattr(
        settings,
        "MODULO_CAPACIDAD_ENABLED",
        False,
    )

    app_prueba = FastAPI()

    assert (
        capacidad_router.incluir_router(app_prueba)
        is False
    )

    assert not any(
        getattr(r, "path", "").startswith(
            "/api/modulo-capacidad"
        )
        for r in app_prueba.routes
    )


def test_flag_encendido_registra_rutas(monkeypatch):
    """El modulo puede activarse por configuracion."""

    monkeypatch.setattr(
        settings,
        "MODULO_CAPACIDAD_ENABLED",
        True,
    )

    app_prueba = FastAPI()

    assert (
        capacidad_router.incluir_router(app_prueba)
        is True
    )

    rutas_openapi = app_prueba.openapi().get("paths", {})

    assert "/api/modulo-capacidad/salud" in rutas_openapi
    assert "get" in rutas_openapi["/api/modulo-capacidad/salud"]



# ============================================================
# 9. PRUEBAS ADICIONALES SEMANAS 9 Y 10
# ============================================================

def test_calculo_con_filtros_ya_no_devuelve_422():
    """Los filtros son un origen valido de pedidos."""

    datos = CalculoRequest(
        modelo_id="toyota-hilux-2024",
        filtros={
            "estado": "LISTO_PARA_ENVIO",
            "distrito": "Lima",
            "limite": 100,
        },
    )

    assert datos.filtros.estado == "LISTO_PARA_ENVIO"
    assert datos.filtros.limite == 100


def test_calculo_no_acepta_origenes_simultaneos():
    """No permite mezclar cajas manuales y filtros."""

    with pytest.raises(ValidationError):
        CalculoRequest(
            modelo_id="toyota-hilux-2024",
            cantidades={"S": 1},
            filtros={},
        )


def test_cantidad_total_mayor_que_5000_se_rechaza():
    """No permite procesar mas de 5000 cajas."""

    with pytest.raises(ValidationError):
        CalculoRequest(
            modelo_id="toyota-hilux-2024",
            cantidades={
                "S": 3000,
                "M": 3000,
            },
        )


def test_sin_vehiculos_pedidos_sin_asignar():
    """Sin flota disponible todos quedan pendientes."""

    plan = _plan(
        capacidad_service.items_demo(700),
        [],
    )

    assert (
        plan["resumen"]["pedidos_sin_asignar"]
        == 700
    )

    assert (
        plan["resumen"]["vehiculos_disponibles"]
        == 0
    )

    assert (
        plan["resumen"]["vehiculos_necesarios"]
        is None
    )

    assert not plan["viajes"]


def test_tamanos_se_guardan_en_configuracion(db):
    """Los tamanos S/M/L son configurables."""

    respuesta = capacidad_service.actualizar_configuracion(
        db,
        ConfiguracionUpdateRequest(
            s_peso_kg=6,
            s_volumen_m3=0.04,
        ),
        "admin@siol.com",
    )

    assert respuesta.s_peso_kg == 6

    db.expire_all()

    config = capacidad_service.obtener_configuracion(db)

    tamanos = capacidad_service.tamanos_desde_config(
        config
    )

    assert tamanos["S"]["volumen_m3"] == 0.04

    cajas = capacidad_service.items_desde_cantidades(
        {"S": 2},
        tamanos,
    )

    assert cajas[0]["peso_kg"] == 6


def test_plan_no_publica_coordenadas_de_pedidos():
    """El resultado no publica coordenadas geograficas."""

    items = [
        {
            "pedido_id": 1,
            "codigo": "PD-001",
            "distrito": "Surco",
            "latitud": -12.14,
            "longitud": -76.99,
            "peso_kg": 5.0,
            "volumen_m3": 0.03,
            "estimado": False,
        }
    ]

    plan = _plan(
        items,
        [_camion()],
    )

    assert plan["resumen"]["pedidos_sin_asignar"] == 0

    pedido = plan["viajes"][0]["pedidos"][0]

    assert "latitud" not in pedido
    assert "longitud" not in pedido


def test_plan_separa_distritos_con_capacidad_suficiente():
    """Un viaje conserva su agrupacion por distrito."""

    items = [
        {
            "pedido_id": i,
            "codigo": f"PD-{i:03d}",
            "distrito": (
                "Surco"
                if i <= 10
                else "Miraflores"
            ),
            "peso_kg": 5.0,
            "volumen_m3": 0.03,
            "estimado": False,
        }
        for i in range(1, 21)
    ]

    plan = _plan(
        items,
        [_camion()],
        paradas=10,
    )

    assert plan["resumen"]["pedidos_sin_asignar"] == 0

    for viaje in plan["viajes"]:
        assert (
            len({
                pedido["distrito"]
                for pedido in viaje["pedidos"]
            })
            == 1
        )


def test_plan_respeta_peso_volumen_y_jornada():
    """Respeta peso, volumen, paradas y jornada."""

    vehiculos = [
        _camion(f"T-{i:02d}")
        for i in range(1, 7)
    ]

    plan = _plan(
        capacidad_service.items_demo(500),
        vehiculos,
        paradas=25,
    )

    for viaje in plan["viajes"]:
        assert viaje["paradas"] <= 25

        assert (
            viaje["peso_kg"]
            <= viaje["capacidad_kg"] + 0.01
        )

        assert (
            viaje["volumen_m3"]
            <= viaje["capacidad_m3"] + 0.01
        )

    for vehiculo in plan["vehiculos"]:
        assert vehiculo["paradas"] <= 60


# ============================================================
# 10. NUEVA PRUEBA: SAN BORJA
# ============================================================

def test_san_borja_cuatro_pedidos_distintas_celdas_un_viaje():
    """
    Cuatro pedidos pequenos en diferentes celdas
    de San Borja deben poder compartir un viaje.
    """

    items = [
        {
            "pedido_id": indice,
            "codigo": f"TEST-SB-{indice}",
            "distrito": "San Borja",
            "latitud": -12.09 - indice * 0.011,
            "longitud": -77.00 + indice * 0.012,
            "peso_kg": 2.5,
            "volumen_m3": 0.02,
            "estimado": False,
        }
        for indice in range(1, 5)
    ]

    plan = _plan(
        items,
        [_camion()],
        paradas=25,
        viajes=3,
    )

    assert plan["resumen"]["total_pedidos"] == 4
    assert plan["resumen"]["pedidos_sin_asignar"] == 0
    assert plan["resumen"]["viajes_necesarios"] == 1

    assert plan["viajes"][0]["paradas"] == 4

    assert (
        len({
            p["pedido_id"]
            for p in plan["viajes"][0]["pedidos"]
        })
        == 4
    )

    assert all(
        "latitud" not in p
        and "longitud" not in p
        for p in plan["viajes"][0]["pedidos"]
    )


# ============================================================
# 11. NUEVA PRUEBA: LIMITES CON VARIAS CELDAS
# ============================================================

def test_varias_celdas_no_rompen_los_limites_de_carga():
    """
    Combinar diferentes celdas nunca debe
    superar el peso o volumen del vehiculo.
    """

    items = [
        {
            "pedido_id": indice,
            "codigo": f"TEST-SB-{indice}",
            "distrito": "San Borja",
            "latitud": -12.1 + indice * 0.01,
            "longitud": -77.01 - indice * 0.01,
            "peso_kg": 50.0,
            "volumen_m3": 0.5,
            "estimado": False,
        }
        for indice in range(1, 6)
    ]

    vehiculo = _camion(
        volumen=1.0,
        carga=100.0,
    )

    plan = _plan(
        items,
        [vehiculo],
        factor=0.85,
        paradas=25,
        viajes=3,
    )

    asignados = sum(
        v["paradas"]
        for v in plan["viajes"]
    )

    pendientes = plan["resumen"]["pedidos_sin_asignar"]

    assert asignados + pendientes == 5

    assert all(
        v["peso_kg"] <= v["capacidad_kg"] + 0.01
        for v in plan["viajes"]
    )

    assert all(
        v["volumen_m3"] <= v["capacidad_m3"] + 0.01
        for v in plan["viajes"]
    )

    assert len(plan["viajes"]) <= 3
