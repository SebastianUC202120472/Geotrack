# Pruebas de la semana 14 del modulo de mantenimiento (Idea 4).
# Usan SQLite en memoria. Las rutas y las incidencias solo se leen.
from datetime import date, datetime, timedelta

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base
from app.models.conductor import PerfilConductor
from app.models.incidencia import Incidencia
from app.models.mantenimiento import (
    AuditoriaMantenimiento,
    CargaCombustible,
    ConfiguracionMantenimiento,
    DocumentoFlota,
    MantenimientoRegistro,
    PlanPreventivo,
)
from app.models.ruta import Ruta
from app.models.usuario import Usuario
from app.models.vehiculo import Vehiculo
from app.schemas.mantenimiento import (
    CargaCombustibleCreateRequest,
    EstadoMantenimientoEnum,
    MantenimientoCreateRequest,
    PreventivoCreateRequest,
    TipoCombustibleEnum,
)
from app.services import mantenimiento_service

HOY = date.today()

TABLAS = [
    Usuario.__table__,
    Vehiculo.__table__,
    PerfilConductor.__table__,
    Ruta.__table__,
    Incidencia.__table__,
    DocumentoFlota.__table__,
    MantenimientoRegistro.__table__,
    PlanPreventivo.__table__,
    CargaCombustible.__table__,
    ConfiguracionMantenimiento.__table__,
    AuditoriaMantenimiento.__table__,
]


@pytest.fixture()
def db():
    """Sesion SQLite en memoria con las tablas que usa esta semana."""

    # StaticPool comparte la unica conexion con los hilos del router ASGI.
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine, tables=TABLAS)
    sesion = sessionmaker(bind=engine)()
    try:
        yield sesion
    finally:
        sesion.close()


def _vehiculo(db, placa="ABC-789"):
    """Crea una unidad activa de prueba. Recibe la sesion y la placa."""

    vehiculo = Vehiculo(placa=placa, marca="Toyota", estado="DISPONIBLE")
    db.add(vehiculo)
    db.commit()
    db.refresh(vehiculo)
    return vehiculo


def _ruta(db, placa="ABC-789", km=100.0, fin=None):
    """Crea una ruta finalizada con kilometraje. Solo lectura desde el modulo."""

    ruta = Ruta(
        nombre="Ruta de prueba",
        estado="FINALIZADA",
        vehiculo_placa=placa,
        km_estimado=km,
        fecha_fin=fin or datetime.utcnow(),
    )
    db.add(ruta)
    db.commit()
    db.refresh(ruta)
    return ruta


def _incidencia(db, ruta, placa="ABC-789", estado="ABIERTA", cuando=None):
    """Crea una incidencia de auxilio mecanico de prueba."""

    incidencia = Incidencia(
        ruta_id=ruta.id,
        conductor_id=1,
        vehiculo_placa=placa,
        tipo="AVERIA_MECANICA",
        estado=estado,
        creado_en=cuando or datetime.utcnow(),
    )
    db.add(incidencia)
    db.commit()
    return incidencia


def _plan(**extra):
    """Arma una peticion valida de plan preventivo."""

    datos = {
        "placa": "ABC-789",
        "categoria": "ACEITE",
        "descripcion": "Cambio de aceite y filtro",
        "intervalo_km": 2000,
        "intervalo_dias": 90,
        "km_base": 0,
        "fecha_base": HOY - timedelta(days=10),
    }
    datos.update(extra)
    return PreventivoCreateRequest(**datos)


def _carga(fecha, odometro, galones=10, monto=100, **extra):
    """Arma una peticion valida de carga de combustible."""

    return CargaCombustibleCreateRequest(
        placa="ABC-789",
        fecha=fecha,
        tipo_combustible=TipoCombustibleEnum.DIESEL,
        galones=galones,
        monto=monto,
        odometro=odometro,
        **extra,
    )


# ---------------------------------------------------------------------------
# Preventivos con km de rutas
# ---------------------------------------------------------------------------


def test_preventivo_usa_km_de_rutas_finalizadas(db):
    """El km del plan sale de las rutas finalizadas, sin escribir en el nucleo."""

    _vehiculo(db)
    _ruta(db, km=1800)
    resultado = mantenimiento_service.crear_preventivo(db, _plan(), "admin@siol.com")
    assert resultado["codigo"] == "PV-001"
    assert resultado["km_actual"] == 1800
    assert resultado["km_restantes"] == 200
    assert resultado["estado"] == "PROXIMO"


def test_preventivo_vencido_por_km(db):
    """Un plan se marca VENCIDO cuando se agota el intervalo de kilometraje."""

    _vehiculo(db)
    _ruta(db, km=2100)
    resultado = mantenimiento_service.crear_preventivo(db, _plan(), "admin@siol.com")
    assert resultado["km_restantes"] == 0
    assert resultado["estado"] == "VENCIDO"


def test_preventivo_sin_lecturas(db):
    """Sin rutas ni odometro el plan queda SIN_LECTURAS, no vencido."""

    _vehiculo(db)
    resultado = mantenimiento_service.crear_preventivo(
        db, _plan(fecha_base=None, intervalo_dias=None), "admin@siol.com"
    )
    assert resultado["estado"] == "SIN_LECTURAS"
    assert resultado["km_restantes"] == 2000


def test_preventivo_invalido(db):
    """El intervalo debe ser positivo."""

    with pytest.raises(ValidationError):
        _plan(intervalo_km=0)


# ---------------------------------------------------------------------------
# Averias
# ---------------------------------------------------------------------------


def test_ranking_averias_sugiere_revision(db):
    """Tres averias en una unidad sugieren revision preventiva."""

    _vehiculo(db)
    ruta = _ruta(db)
    _incidencia(db, ruta, estado="ABIERTA")
    _incidencia(db, ruta, estado="ABIERTA")
    _incidencia(db, ruta, estado="RESUELTA")
    ranking = mantenimiento_service.ranking_averias(db)
    assert ranking[0]["placa"] == "ABC-789"
    assert ranking[0]["total"] == 3
    assert ranking[0]["abiertas"] == 2
    assert ranking[0]["sugerencia"] == "Revisión preventiva sugerida"


# ---------------------------------------------------------------------------
# Combustible y costos
# ---------------------------------------------------------------------------


def test_carga_calcula_rendimiento_y_consumo_anomalo(db):
    """El rendimiento sale del odometro y el desvio marca consumo anomalo."""

    _vehiculo(db)
    _ruta(db, km=200, fin=HOY - timedelta(days=15))
    mantenimiento_service.crear_carga(
        db, _carga(HOY - timedelta(days=10), 1000, galones=10), "admin@siol.com"
    )
    segunda = mantenimiento_service.crear_carga(
        db, _carga(HOY, 1200, galones=20), "admin@siol.com"
    )
    cargas = mantenimiento_service.listar_cargas(db)
    assert cargas[0]["rendimiento_km_gal"] == 20.0
    assert cargas[1]["rendimiento_km_gal"] == 10.0
    assert segunda["consumo_anomalo"] is True


def test_kilometraje_no_puede_retroceder(db):
    """Una lectura menor que la ultima se rechaza con 422."""

    _vehiculo(db)
    mantenimiento_service.crear_carga(db, _carga(HOY - timedelta(days=1), 1200), "admin@siol.com")
    with pytest.raises(HTTPException) as error:
        mantenimiento_service.crear_carga(db, _carga(HOY, 1100), "admin@siol.com")
    assert error.value.status_code == 422


def test_costos_incluyen_combustible_y_mantenimiento(db):
    """El costo total suma taller y combustible."""

    _vehiculo(db)
    mantenimiento_service.crear_mantenimiento(
        db,
        MantenimientoCreateRequest(
            placa="ABC-789",
            descripcion="Cambio de aceite",
            estado=EstadoMantenimientoEnum.COMPLETADO,
            fecha_programada=HOY,
            fecha_ejecucion=HOY,
            costo=320.5,
            kilometraje=1000,
        ),
        "admin@siol.com",
    )
    mantenimiento_service.crear_carga(db, _carga(HOY, 1200, monto=80), "admin@siol.com")
    costos = mantenimiento_service.costos_flota(db)
    assert costos["costo_mantenimiento"] == 320.5
    assert costos["costo_combustible"] == 80.0
    assert costos["costo_total"] == 400.5
    assert costos["cargas_totales"] == 1


def test_ficha_incluye_nuevas_secciones(db):
    """La ficha de unidad trae preventivos, cargas y averias."""

    _vehiculo(db)
    ruta = _ruta(db)
    _incidencia(db, ruta)
    mantenimiento_service.crear_preventivo(db, _plan(), "admin@siol.com")
    mantenimiento_service.crear_carga(db, _carga(HOY, 1200), "admin@siol.com")
    ficha = mantenimiento_service.ficha_vehiculo(db, "ABC-789")
    assert len(ficha["preventivos"]) == 1
    assert len(ficha["cargas"]) == 1
    assert len(ficha["averias"]) == 1
    assert ficha["costos"]["costo_combustible"] == 100.0


def test_alertas_incluyen_preventivo_vencido(db):
    """Un preventivo vencido aparece en las alertas del dia."""

    _vehiculo(db)
    _ruta(db, km=3000)
    mantenimiento_service.crear_preventivo(db, _plan(), "admin@siol.com")
    alertas = mantenimiento_service.alertas(db)
    assert any(
        aviso["tipo"] == "PREVENTIVO" and aviso["severidad"] == "ALTA"
        for aviso in alertas
    )


def test_resumen_incluye_indicadores_de_la_semana_14(db):
    """El resumen reporta preventivos vencidos, combustible y rendimiento."""

    _vehiculo(db)
    _ruta(db, km=2500)
    mantenimiento_service.crear_preventivo(db, _plan(), "admin@siol.com")
    mantenimiento_service.crear_carga(db, _carga(HOY, 1200, monto=75), "admin@siol.com")
    resumen = mantenimiento_service.resumen(db)
    assert resumen["preventivos_vencidos"] == 1
    assert resumen["costo_combustible"] == 75.0
    assert resumen["costo_total"] == 0.0  # el historico sigue siendo solo taller
    assert resumen["costo_por_kilometro"] is not None
    assert resumen["rendimiento_km_gal"] == 250.0


def test_endpoints_nuevos_responden(db):
    """Los endpoints de la semana 14 responden con sus modelos de respuesta."""

    import asyncio
    from types import SimpleNamespace

    import httpx
    from fastapi import FastAPI

    from app.api import mantenimiento as mantenimiento_api
    from app.api.deps import get_current_admin, get_current_almacen
    from app.db.database import get_db

    _vehiculo(db)
    aplicacion = FastAPI()
    aplicacion.include_router(
        mantenimiento_api.router, prefix="/api/modulo-mantenimiento"
    )
    usuario = SimpleNamespace(correo="admin@siol.com", rol="admin")
    aplicacion.dependency_overrides[get_db] = lambda: db
    aplicacion.dependency_overrides[get_current_admin] = lambda: usuario
    aplicacion.dependency_overrides[get_current_almacen] = lambda: usuario
    base = "/api/modulo-mantenimiento"
    plan = {
        "placa": "ABC-789",
        "categoria": "ACEITE",
        "descripcion": "Cambio de aceite y filtro",
        "intervalo_km": 2000,
    }
    carga = {
        "placa": "ABC-789",
        "fecha": HOY.isoformat(),
        "galones": 10,
        "monto": 100,
        "odometro": 1000,
    }

    async def consultar():
        transporte = httpx.ASGITransport(app=aplicacion)
        async with httpx.AsyncClient(
            transport=transporte, base_url="http://prueba"
        ) as cliente:
            assert (await cliente.get(f"{base}/preventivos")).status_code == 200
            assert (
                await cliente.post(f"{base}/preventivos", json=plan)
            ).status_code == 201
            assert (await cliente.get(f"{base}/averias/ranking")).status_code == 200
            assert (
                await cliente.post(f"{base}/combustible", json=carga)
            ).status_code == 201
            assert (await cliente.get(f"{base}/combustible")).status_code == 200
            assert (await cliente.get(f"{base}/costos")).status_code == 200
            assert (await cliente.get(f"{base}/resumen")).status_code == 200

    asyncio.run(consultar())


def test_carga_invalida(db):
    """Los galones y el monto deben ser positivos."""

    with pytest.raises(ValidationError):
        _carga(HOY, 1000, galones=0)
    with pytest.raises(ValidationError):
        _carga(HOY, 1000, monto=-1)
