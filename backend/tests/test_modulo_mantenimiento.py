# Pruebas del modulo de mantenimiento y documentos de la flota (Idea 4).
# No necesitan PostgreSQL: usan SQLite en memoria y funciones puras.
from datetime import date, timedelta

import pytest
from fastapi import FastAPI, HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api import mantenimiento as mantenimiento_router
from app.core.config import settings
from app.db.database import Base
from app.models.conductor import PerfilConductor
from app.models.mantenimiento import (
    AuditoriaMantenimiento,
    ConfiguracionMantenimiento,
    DocumentoFlota,
    MantenimientoRegistro,
)
from app.models.usuario import Usuario
from app.models.vehiculo import Vehiculo
from app.schemas.mantenimiento import (
    CompletarMantenimientoRequest,
    ConfiguracionUpdateRequest,
    DocumentoCreateRequest,
    DocumentoUpdateRequest,
    EstadoDocumentoEnum,
    EstadoMantenimientoEnum,
    MantenimientoCreateRequest,
    MantenimientoUpdateRequest,
    TipoDocumentoEnum,
    TipoMantenimientoEnum,
)
from app.services import mantenimiento_service

HOY = date.today()

TABLAS = [
    Usuario.__table__,
    Vehiculo.__table__,
    PerfilConductor.__table__,
    DocumentoFlota.__table__,
    MantenimientoRegistro.__table__,
    ConfiguracionMantenimiento.__table__,
    AuditoriaMantenimiento.__table__,
]


@pytest.fixture()
def db():
    """Sesion SQLite en memoria con las tablas del nucleo y del modulo."""

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine, tables=TABLAS)
    sesion = sessionmaker(bind=engine)()
    try:
        yield sesion
    finally:
        sesion.close()


# ---------------------------------------------------------------------------
# Datos de apoyo
# ---------------------------------------------------------------------------


def _vehiculo(db, placa="ABC-123", marca="Toyota"):
    """Crea un vehiculo activo de prueba y lo devuelve."""

    vehiculo = Vehiculo(placa=placa, marca=marca, estado="DISPONIBLE")
    db.add(vehiculo)
    db.commit()
    db.refresh(vehiculo)
    return vehiculo


def _documento(
    placa="ABC-123",
    tipo=TipoDocumentoEnum.SOAT,
    numero="SOAT-001",
    vencimiento=None,
    emision=None,
):
    """Arma un documento valido de prueba."""

    return DocumentoCreateRequest(
        placa=placa,
        tipo_documento=tipo,
        numero=numero,
        entidad_emisora="La Positiva",
        fecha_emision=emision or (HOY - timedelta(days=365)),
        fecha_vencimiento=vencimiento or (HOY + timedelta(days=365)),
    )


def _mantenimiento(
    placa="ABC-123",
    fecha=None,
    estado=EstadoMantenimientoEnum.PROGRAMADO,
    tipo=TipoMantenimientoEnum.PREVENTIVO,
    **extra,
):
    """Arma un mantenimiento valido de prueba."""

    return MantenimientoCreateRequest(
        placa=placa,
        descripcion="Cambio de aceite y filtros",
        tipo=tipo,
        estado=estado,
        fecha_programada=fecha or (HOY + timedelta(days=3)),
        **extra,
    )


def _conductor(
    db,
    nombre="Ana Torres",
    vencimiento=None,
    numero="Q12345678",
):
    """Crea un conductor con su perfil y licencia de prueba."""

    usuario = Usuario(
        correo=f"conductor{db.query(Usuario).count()}@siol.com",
        hash_contrasena="x",
        rol="conductor",
        nombre=nombre,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)

    perfil = PerfilConductor(
        usuario_id=usuario.id,
        nombre=nombre,
        dni="12345678",
        licencia_numero=numero,
        licencia_vencimiento=vencimiento,
    )
    db.add(perfil)
    db.commit()
    db.refresh(perfil)
    return perfil


# ---------------------------------------------------------------------------
# 1. Reglas de estado (funciones puras)
# ---------------------------------------------------------------------------


def test_documento_vencido():
    """Un vencimiento anterior a hoy se marca VENCIDO."""

    assert (
        mantenimiento_service.calcular_estado_documento(
            HOY - timedelta(days=1), HOY, 30
        )
        == EstadoDocumentoEnum.VENCIDO.value
    )


def test_documento_que_vence_hoy_esta_por_vencer():
    """El mismo dia del vencimiento todavia es POR_VENCER, no VENCIDO."""

    assert (
        mantenimiento_service.calcular_estado_documento(HOY, HOY, 30)
        == EstadoDocumentoEnum.POR_VENCER.value
    )


def test_documento_en_el_limite_de_aviso():
    """Exactamente en el dia limite sigue siendo POR_VENCER."""

    assert (
        mantenimiento_service.calcular_estado_documento(
            HOY + timedelta(days=30), HOY, 30
        )
        == EstadoDocumentoEnum.POR_VENCER.value
    )


def test_documento_fuera_del_aviso_es_vigente():
    """Un dia despues del limite ya es VIGENTE."""

    assert (
        mantenimiento_service.calcular_estado_documento(
            HOY + timedelta(days=31), HOY, 30
        )
        == EstadoDocumentoEnum.VIGENTE.value
    )


def test_dias_para_vencer_negativo():
    """Los dias restantes son negativos cuando ya vencio."""

    assert (
        mantenimiento_service.dias_para_vencer(HOY - timedelta(days=5), HOY) == -5
    )


# ---------------------------------------------------------------------------
# 2. Validaciones de esquemas
# ---------------------------------------------------------------------------


def test_placa_invalida():
    """Una placa sin el formato ABC-123 se rechaza."""

    with pytest.raises(ValidationError):
        _documento(placa="ABC123")


def test_placa_se_normaliza_a_mayusculas():
    """La placa se guarda en mayusculas y sin espacios."""

    documento = _documento(placa=" abc-123 ")
    assert documento.placa == "ABC-123"


def test_fechas_incoherentes():
    """El vencimiento no puede ser anterior o igual a la emision."""

    with pytest.raises(ValidationError):
        _documento(emision=HOY, vencimiento=HOY)


def test_numero_vacio_se_rechaza():
    """El numero de documento no puede quedar vacio."""

    with pytest.raises(ValidationError):
        _documento(numero="")


def test_costo_negativo_se_rechaza():
    """El costo de un mantenimiento no puede ser negativo."""

    with pytest.raises(ValidationError):
        _mantenimiento(costo=-1)


def test_mantenimiento_completado_exige_fecha():
    """Si nace COMPLETADO, debe indicar la fecha de ejecucion."""

    with pytest.raises(ValidationError):
        _mantenimiento(estado=EstadoMantenimientoEnum.COMPLETADO)


# ---------------------------------------------------------------------------
# 3. Documentos: alta, consulta, edicion y baja
# ---------------------------------------------------------------------------


def test_crear_documento_asigna_codigo_y_audita(db):
    """El primer documento recibe DC-001 y deja rastro en auditoria."""

    _vehiculo(db)
    resultado = mantenimiento_service.crear_documento(
        db, _documento(), "admin@siol.com"
    )

    assert resultado["codigo"] == "DC-001"
    assert resultado["estado"] == EstadoDocumentoEnum.VIGENTE.value
    assert resultado["dias_para_vencer"] == 365
    assert db.query(DocumentoFlota).count() == 1

    auditoria = mantenimiento_service.historial_auditoria(db)
    assert auditoria[0]["accion"] == "crear"
    assert auditoria[0]["entidad"] == "documento"
    assert auditoria[0]["usuario"] == "admin@siol.com"


def test_crear_documento_de_vehiculo_inexistente(db):
    """No se puede documentar una placa que no existe en la flota."""

    with pytest.raises(HTTPException) as error:
        mantenimiento_service.crear_documento(
            db, _documento(placa="ZZZ-999"), "admin@siol.com"
        )

    assert error.value.status_code == 404


def test_crear_documento_duplicado(db):
    """El mismo tipo y numero para la misma placa se rechaza."""

    _vehiculo(db)
    mantenimiento_service.crear_documento(db, _documento(), "admin@siol.com")

    with pytest.raises(HTTPException) as error:
        mantenimiento_service.crear_documento(db, _documento(), "admin@siol.com")

    assert error.value.status_code == 409


def test_renovacion_con_otro_numero_se_permite(db):
    """Una renovacion del mismo tipo con otro numero si se registra."""

    _vehiculo(db)
    mantenimiento_service.crear_documento(db, _documento(), "admin@siol.com")
    mantenimiento_service.crear_documento(
        db, _documento(numero="SOAT-002"), "admin@siol.com"
    )

    assert db.query(DocumentoFlota).count() == 2


def test_listar_documentos_por_estado(db):
    """El filtro por estado usa la fecha de vencimiento y los dias de aviso."""

    _vehiculo(db)
    mantenimiento_service.crear_documento(
        db, _documento(numero="SOAT-VIG"), "admin@siol.com"
    )
    mantenimiento_service.crear_documento(
        db,
        _documento(
            numero="SOAT-POR",
            emision=HOY - timedelta(days=300),
            vencimiento=HOY + timedelta(days=10),
        ),
        "admin@siol.com",
    )
    mantenimiento_service.crear_documento(
        db,
        _documento(
            numero="SOAT-VEN",
            emision=HOY - timedelta(days=400),
            vencimiento=HOY - timedelta(days=5),
        ),
        "admin@siol.com",
    )

    vencidos = mantenimiento_service.listar_documentos(
        db, estado=EstadoDocumentoEnum.VENCIDO
    )
    por_vencer = mantenimiento_service.listar_documentos(
        db, estado=EstadoDocumentoEnum.POR_VENCER
    )
    vigentes = mantenimiento_service.listar_documentos(
        db, estado=EstadoDocumentoEnum.VIGENTE
    )

    assert [fila["numero"] for fila in vencidos] == ["SOAT-VEN"]
    assert [fila["numero"] for fila in por_vencer] == ["SOAT-POR"]
    assert [fila["numero"] for fila in vigentes] == ["SOAT-VIG"]


def test_listar_documentos_por_tipo_y_placa(db):
    """Los filtros por tipo y placa se combinan."""

    _vehiculo(db, placa="ABC-123")
    _vehiculo(db, placa="DEF-456")
    mantenimiento_service.crear_documento(db, _documento(), "admin@siol.com")
    mantenimiento_service.crear_documento(
        db,
        _documento(
            tipo=TipoDocumentoEnum.REVISION_TECNICA, numero="RT-001"
        ),
        "admin@siol.com",
    )
    mantenimiento_service.crear_documento(
        db,
        _documento(placa="DEF-456", numero="SOAT-999"),
        "admin@siol.com",
    )

    filtrados = mantenimiento_service.listar_documentos(
        db, placa="abc-123", tipo=TipoDocumentoEnum.SOAT
    )

    assert len(filtrados) == 1
    assert filtrados[0]["numero"] == "SOAT-001"


def test_actualizar_documento(db):
    """Se puede corregir el numero y las observaciones de un documento."""

    _vehiculo(db)
    creado = mantenimiento_service.crear_documento(
        db, _documento(), "admin@siol.com"
    )
    actualizado = mantenimiento_service.actualizar_documento(
        db,
        creado["id"],
        DocumentoUpdateRequest(numero="SOAT-777", observaciones="Corregido"),
        "admin@siol.com",
    )

    assert actualizado["numero"] == "SOAT-777"
    assert actualizado["observaciones"] == "Corregido"
    assert actualizado["actualizado_por"] == "admin@siol.com"


def test_actualizar_documento_con_fechas_incoherentes(db):
    """La validacion de fechas tambien se aplica al editar."""

    _vehiculo(db)
    creado = mantenimiento_service.crear_documento(
        db, _documento(), "admin@siol.com"
    )

    with pytest.raises(HTTPException) as error:
        mantenimiento_service.actualizar_documento(
            db,
            creado["id"],
            DocumentoUpdateRequest(fecha_vencimiento=HOY - timedelta(days=500)),
            "admin@siol.com",
        )

    assert error.value.status_code == 422


def test_actualizar_documento_a_duplicado(db):
    """No se puede editar un documento para dejarlo duplicado."""

    _vehiculo(db)
    mantenimiento_service.crear_documento(db, _documento(), "admin@siol.com")
    segundo = mantenimiento_service.crear_documento(
        db, _documento(numero="SOAT-002"), "admin@siol.com"
    )

    with pytest.raises(HTTPException) as error:
        mantenimiento_service.actualizar_documento(
            db,
            segundo["id"],
            DocumentoUpdateRequest(numero="SOAT-001"),
            "admin@siol.com",
        )

    assert error.value.status_code == 409


def test_eliminar_documento_es_baja_logica(db):
    """El documento borrado no se lista ni se puede consultar, pero queda la fila."""

    _vehiculo(db)
    creado = mantenimiento_service.crear_documento(
        db, _documento(), "admin@siol.com"
    )
    mantenimiento_service.eliminar_documento(db, creado["id"], "admin@siol.com")

    assert mantenimiento_service.listar_documentos(db) == []
    with pytest.raises(HTTPException) as error:
        mantenimiento_service.obtener_documento(db, creado["id"])
    assert error.value.status_code == 404
    assert db.query(DocumentoFlota).count() == 1
    assert db.query(DocumentoFlota).first().eliminado_en is not None


def test_obtener_documento_inexistente(db):
    """Un id que no existe responde 404."""

    with pytest.raises(HTTPException) as error:
        mantenimiento_service.obtener_documento(db, 999)
    assert error.value.status_code == 404


# ---------------------------------------------------------------------------
# 4. Mantenimientos
# ---------------------------------------------------------------------------


def test_crear_mantenimiento_asigna_codigo(db):
    """El primer mantenimiento recibe MT-001 y la moneda de la configuracion."""

    _vehiculo(db)
    resultado = mantenimiento_service.crear_mantenimiento(
        db, _mantenimiento(), "admin@siol.com"
    )

    assert resultado["codigo"] == "MT-001"
    assert resultado["estado"] == EstadoMantenimientoEnum.PROGRAMADO.value
    assert resultado["moneda"] == "PEN"
    assert resultado["vencido"] is False
    assert resultado["dias_para_programado"] == 3


def test_crear_mantenimiento_de_vehiculo_inexistente(db):
    """No se puede programar mantenimiento para una placa que no existe."""

    with pytest.raises(HTTPException) as error:
        mantenimiento_service.crear_mantenimiento(
            db, _mantenimiento(placa="ZZZ-999"), "admin@siol.com"
        )
    assert error.value.status_code == 404


def test_mantenimiento_atrasado_se_marca_vencido(db):
    """Un mantenimiento abierto con fecha pasada aparece vencido."""

    _vehiculo(db)
    mantenimiento_service.crear_mantenimiento(
        db, _mantenimiento(fecha=HOY - timedelta(days=2)), "admin@siol.com"
    )

    fila = mantenimiento_service.listar_mantenimientos(db)[0]
    assert fila["vencido"] is True
    assert fila["dias_para_programado"] == -2


def test_completar_mantenimiento(db):
    """Completar guarda fecha, costo, kilometraje y deja de estar vencido."""

    _vehiculo(db)
    creado = mantenimiento_service.crear_mantenimiento(
        db, _mantenimiento(fecha=HOY - timedelta(days=1)), "admin@siol.com"
    )
    completado = mantenimiento_service.completar_mantenimiento(
        db,
        creado["id"],
        CompletarMantenimientoRequest(costo=250.5, kilometraje=15000),
        "admin@siol.com",
    )

    assert completado["estado"] == EstadoMantenimientoEnum.COMPLETADO.value
    assert completado["fecha_ejecucion"] == HOY
    assert completado["costo"] == 250.5
    assert completado["kilometraje"] == 15000
    assert completado["vencido"] is False


def test_no_se_puede_completar_dos_veces(db):
    """Un mantenimiento ya completado responde 409."""

    _vehiculo(db)
    creado = mantenimiento_service.crear_mantenimiento(
        db, _mantenimiento(), "admin@siol.com"
    )
    mantenimiento_service.completar_mantenimiento(
        db, creado["id"], CompletarMantenimientoRequest(), "admin@siol.com"
    )

    with pytest.raises(HTTPException) as error:
        mantenimiento_service.completar_mantenimiento(
            db, creado["id"], CompletarMantenimientoRequest(), "admin@siol.com"
        )
    assert error.value.status_code == 409


def test_no_se_puede_completar_un_cancelado(db):
    """Un mantenimiento cancelado no se puede completar."""

    _vehiculo(db)
    creado = mantenimiento_service.crear_mantenimiento(
        db,
        _mantenimiento(estado=EstadoMantenimientoEnum.CANCELADO),
        "admin@siol.com",
    )

    with pytest.raises(HTTPException) as error:
        mantenimiento_service.completar_mantenimiento(
            db, creado["id"], CompletarMantenimientoRequest(), "admin@siol.com"
        )
    assert error.value.status_code == 409


def test_crear_mantenimiento_completado_con_fecha(db):
    """Un registro historico puede nacer completado si trae fecha."""

    _vehiculo(db)
    resultado = mantenimiento_service.crear_mantenimiento(
        db,
        _mantenimiento(
            estado=EstadoMantenimientoEnum.COMPLETADO,
            fecha=HOY - timedelta(days=10),
            fecha_ejecucion=HOY - timedelta(days=9),
            costo=180,
        ),
        "admin@siol.com",
    )

    assert resultado["estado"] == EstadoMantenimientoEnum.COMPLETADO.value
    assert resultado["fecha_ejecucion"] == HOY - timedelta(days=9)


def test_listar_mantenimientos_con_filtros(db):
    """Los filtros por placa, tipo, estado y rango de fechas funcionan juntos."""

    _vehiculo(db, placa="ABC-123")
    _vehiculo(db, placa="DEF-456")
    mantenimiento_service.crear_mantenimiento(
        db,
        _mantenimiento(fecha=HOY + timedelta(days=1)),
        "admin@siol.com",
    )
    mantenimiento_service.crear_mantenimiento(
        db,
        _mantenimiento(
            placa="DEF-456",
            tipo=TipoMantenimientoEnum.CORRECTIVO,
            fecha=HOY + timedelta(days=20),
        ),
        "admin@siol.com",
    )

    filtrados = mantenimiento_service.listar_mantenimientos(
        db,
        placa="DEF-456",
        tipo=TipoMantenimientoEnum.CORRECTIVO,
        estado=EstadoMantenimientoEnum.PROGRAMADO,
        desde=HOY,
        hasta=HOY + timedelta(days=30),
    )

    assert len(filtrados) == 1
    assert filtrados[0]["placa"] == "DEF-456"
    assert filtrados[0]["tipo"] == "CORRECTIVO"


def test_actualizar_mantenimiento(db):
    """Se puede cambiar la prioridad y la fecha de un mantenimiento."""

    _vehiculo(db)
    creado = mantenimiento_service.crear_mantenimiento(
        db, _mantenimiento(), "admin@siol.com"
    )
    actualizado = mantenimiento_service.actualizar_mantenimiento(
        db,
        creado["id"],
        MantenimientoUpdateRequest(
            prioridad="ALTA", fecha_programada=HOY + timedelta(days=10)
        ),
        "admin@siol.com",
    )

    assert actualizado["prioridad"] == "ALTA"
    assert actualizado["fecha_programada"] == HOY + timedelta(days=10)


def test_eliminar_mantenimiento_es_baja_logica(db):
    """El mantenimiento borrado no se lista, pero la fila queda."""

    _vehiculo(db)
    creado = mantenimiento_service.crear_mantenimiento(
        db, _mantenimiento(), "admin@siol.com"
    )
    mantenimiento_service.eliminar_mantenimiento(
        db, creado["id"], "admin@siol.com"
    )

    assert mantenimiento_service.listar_mantenimientos(db) == []
    with pytest.raises(HTTPException) as error:
        mantenimiento_service.obtener_mantenimiento(db, creado["id"])
    assert error.value.status_code == 404
    assert db.query(MantenimientoRegistro).count() == 1


# ---------------------------------------------------------------------------
# 5. Configuracion y auditoria
# ---------------------------------------------------------------------------


def test_configuracion_por_defecto(db):
    """La primera lectura crea la fila unica con valores seguros."""

    config = mantenimiento_service.obtener_configuracion(db)
    otra = mantenimiento_service.obtener_configuracion(db)

    assert config.id == 1
    assert config.dias_aviso_documento == 30
    assert config.dias_aviso_mantenimiento == 7
    assert config.moneda == "PEN"
    assert config.alertas_documentos is True
    assert config.alertas_mantenimientos is True
    assert otra.id == config.id
    assert db.query(ConfiguracionMantenimiento).count() == 1


def test_actualizar_configuracion_audita(db):
    """Cambiar parametros actualiza la fila y registra la auditoria."""

    resultado = mantenimiento_service.actualizar_configuracion(
        db,
        ConfiguracionUpdateRequest(
            dias_aviso_documento=45,
            moneda="usd",
            alertas_mantenimientos=False,
        ),
        "admin@siol.com",
    )

    assert resultado["dias_aviso_documento"] == 45
    assert resultado["moneda"] == "USD"
    assert resultado["alertas_mantenimientos"] is False
    assert resultado["actualizado_por"] == "admin@siol.com"

    auditoria = mantenimiento_service.historial_auditoria(db)
    assert auditoria[0]["entidad"] == "configuracion"


def test_configuracion_no_acepta_nulos(db):
    """Un null explicito en configuracion responde 422."""

    with pytest.raises(HTTPException) as error:
        mantenimiento_service.actualizar_configuracion(
            db,
            ConfiguracionUpdateRequest(dias_aviso_documento=None),
            "admin@siol.com",
        )
    assert error.value.status_code == 422


def test_historial_auditoria_ordenado(db):
    """La auditoria devuelve primero el movimiento mas reciente."""

    _vehiculo(db)
    mantenimiento_service.crear_documento(db, _documento(), "admin@siol.com")
    mantenimiento_service.crear_mantenimiento(
        db, _mantenimiento(), "admin@siol.com"
    )

    auditoria = mantenimiento_service.historial_auditoria(db)
    assert auditoria[0]["entidad"] == "mantenimiento"
    assert auditoria[1]["entidad"] == "documento"


# ---------------------------------------------------------------------------
# 6. Alertas
# ---------------------------------------------------------------------------


def test_alerta_documento_vencido(db):
    """Un documento vencido genera una alerta ALTA."""

    _vehiculo(db)
    mantenimiento_service.crear_documento(
        db,
        _documento(
            emision=HOY - timedelta(days=400),
            vencimiento=HOY - timedelta(days=3),
        ),
        "admin@siol.com",
    )

    avisos = [
        aviso
        for aviso in mantenimiento_service.alertas(db)
        if aviso["tipo"] == "DOCUMENTO"
    ]

    assert len(avisos) == 1
    assert avisos[0]["severidad"] == "ALTA"
    assert avisos[0]["dias"] == -3


def test_alerta_documento_por_vencer(db):
    """Un documento dentro del aviso genera una alerta MEDIA."""

    _vehiculo(db)
    mantenimiento_service.crear_documento(
        db,
        _documento(
            emision=HOY - timedelta(days=300),
            vencimiento=HOY + timedelta(days=10),
        ),
        "admin@siol.com",
    )

    avisos = [
        aviso
        for aviso in mantenimiento_service.alertas(db)
        if aviso["tipo"] == "DOCUMENTO"
    ]

    assert len(avisos) == 1
    assert avisos[0]["severidad"] == "MEDIA"
    assert avisos[0]["dias"] == 10


def test_alerta_documentos_obligatorios_faltantes(db):
    """Un vehiculo sin SOAT ni revision tecnica genera dos avisos."""

    _vehiculo(db)

    avisos = [
        aviso
        for aviso in mantenimiento_service.alertas(db)
        if aviso["tipo"] == "SIN_DOCUMENTO"
    ]

    assert len(avisos) == 2
    assert {aviso["titulo"] for aviso in avisos} == {
        "Falta SOAT",
        "Falta REVISION_TECNICA",
    }


def test_alerta_mantenimiento_vencido_y_proximo(db):
    """Los mantenimientos abiertos avisan segun su fecha."""

    _vehiculo(db)
    mantenimiento_service.crear_mantenimiento(
        db, _mantenimiento(fecha=HOY - timedelta(days=1)), "admin@siol.com"
    )
    mantenimiento_service.crear_mantenimiento(
        db, _mantenimiento(fecha=HOY + timedelta(days=3)), "admin@siol.com"
    )
    mantenimiento_service.crear_mantenimiento(
        db, _mantenimiento(fecha=HOY + timedelta(days=30)), "admin@siol.com"
    )

    avisos = [
        aviso
        for aviso in mantenimiento_service.alertas(db)
        if aviso["tipo"] == "MANTENIMIENTO"
    ]

    assert len(avisos) == 2
    assert avisos[0]["titulo"] == "Mantenimiento vencido"
    assert avisos[0]["severidad"] == "ALTA"
    assert avisos[1]["titulo"] == "Mantenimiento próximo"
    assert avisos[1]["severidad"] == "MEDIA"


def test_banderas_de_alertas_apagan_grupos(db):
    """Apagar documentos deja solo las alertas de mantenimiento."""

    _vehiculo(db)
    mantenimiento_service.actualizar_configuracion(
        db,
        ConfiguracionUpdateRequest(
            alertas_documentos=False, alertas_mantenimientos=True
        ),
        "admin@siol.com",
    )
    mantenimiento_service.crear_mantenimiento(
        db, _mantenimiento(fecha=HOY - timedelta(days=1)), "admin@siol.com"
    )

    avisos = mantenimiento_service.alertas(db)

    assert avisos
    assert all(aviso["tipo"] == "MANTENIMIENTO" for aviso in avisos)


# ---------------------------------------------------------------------------
# 7. Resumen y estado de la flota
# ---------------------------------------------------------------------------


def test_resumen_cuenta_documentos_y_costos(db):
    """El resumen suma documentos por estado y costos del mes."""

    _vehiculo(db)
    mantenimiento_service.crear_documento(
        db, _documento(numero="SOAT-VIG"), "admin@siol.com"
    )
    mantenimiento_service.crear_documento(
        db,
        _documento(
            tipo=TipoDocumentoEnum.REVISION_TECNICA,
            numero="RT-VEN",
            emision=HOY - timedelta(days=400),
            vencimiento=HOY - timedelta(days=1),
        ),
        "admin@siol.com",
    )
    creado = mantenimiento_service.crear_mantenimiento(
        db, _mantenimiento(), "admin@siol.com"
    )
    mantenimiento_service.completar_mantenimiento(
        db, creado["id"], CompletarMantenimientoRequest(costo=120.25), "admin@siol.com"
    )

    resultado = mantenimiento_service.resumen(db)

    assert resultado["total_vehiculos"] == 1
    assert resultado["documentos_total"] == 2
    assert resultado["documentos_vigentes"] == 1
    assert resultado["documentos_vencidos"] == 1
    assert resultado["documentos_por_tipo"]["SOAT"] == 1
    assert resultado["mantenimientos_completados"] == 1
    assert resultado["costo_mes"] == 120.25
    assert resultado["costo_total"] == 120.25
    assert resultado["alertas_alta"] >= 1
    assert resultado["vehiculos_sin_documentos"] == 0


def test_resumen_cuenta_vehiculos_sin_documentos(db):
    """Un vehiculo sin documentos se cuenta aparte."""

    _vehiculo(db)
    resultado = mantenimiento_service.resumen(db)

    assert resultado["vehiculos_sin_documentos"] == 1
    assert resultado["documentos_total"] == 0


def test_estado_flota_sin_documentos(db):
    """Sin documentos, el vehiculo queda SIN_DOCUMENTOS y con faltantes."""

    _vehiculo(db)
    fila = mantenimiento_service.estado_flota(db)[0]

    assert fila["estado_general"] == "SIN_DOCUMENTOS"
    assert set(fila["documentos_faltantes"]) == {"SOAT", "REVISION_TECNICA"}


def test_estado_flota_al_dia(db):
    """Con SOAT y revision tecnica vigentes, el vehiculo queda AL_DIA."""

    _vehiculo(db)
    mantenimiento_service.crear_documento(db, _documento(), "admin@siol.com")
    mantenimiento_service.crear_documento(
        db,
        _documento(
            tipo=TipoDocumentoEnum.REVISION_TECNICA, numero="RT-001"
        ),
        "admin@siol.com",
    )

    fila = mantenimiento_service.estado_flota(db)[0]

    assert fila["estado_general"] == "AL_DIA"
    assert fila["documentos_faltantes"] == []
    assert fila["documentos_total"] == 2


def test_estado_flota_incompleto(db):
    """Si falta un documento obligatorio, el estado es INCOMPLETO."""

    _vehiculo(db)
    mantenimiento_service.crear_documento(db, _documento(), "admin@siol.com")

    fila = mantenimiento_service.estado_flota(db)[0]

    assert fila["estado_general"] == "INCOMPLETO"
    assert fila["documentos_faltantes"] == ["REVISION_TECNICA"]


def test_estado_flota_vencido(db):
    """Si un documento obligatorio vencio, el estado es VENCIDO."""

    _vehiculo(db)
    mantenimiento_service.crear_documento(
        db,
        _documento(
            emision=HOY - timedelta(days=400),
            vencimiento=HOY - timedelta(days=1),
        ),
        "admin@siol.com",
    )
    mantenimiento_service.crear_documento(
        db,
        _documento(
            tipo=TipoDocumentoEnum.REVISION_TECNICA,
            numero="RT-001",
        ),
        "admin@siol.com",
    )

    fila = mantenimiento_service.estado_flota(db)[0]

    assert fila["estado_general"] == "VENCIDO"
    assert fila["documentos_vencidos"] == 1


def test_estado_flota_por_vencer(db):
    """Si los documentos estan dentro del aviso, el estado es POR_VENCER."""

    _vehiculo(db)
    mantenimiento_service.crear_documento(
        db,
        _documento(
            emision=HOY - timedelta(days=300),
            vencimiento=HOY + timedelta(days=10),
        ),
        "admin@siol.com",
    )
    mantenimiento_service.crear_documento(
        db,
        _documento(
            tipo=TipoDocumentoEnum.REVISION_TECNICA,
            numero="RT-001",
            emision=HOY - timedelta(days=300),
            vencimiento=HOY + timedelta(days=15),
        ),
        "admin@siol.com",
    )

    fila = mantenimiento_service.estado_flota(db)[0]

    assert fila["estado_general"] == "POR_VENCER"
    assert fila["documentos_por_vencer"] == 2
    assert fila["proximo_vencimiento"] == HOY + timedelta(days=10)


def test_estado_flota_cuenta_mantenimientos_abiertos(db):
    """El estado de flota cuenta los mantenimientos abiertos y el proximo."""

    _vehiculo(db)
    mantenimiento_service.crear_mantenimiento(
        db, _mantenimiento(fecha=HOY + timedelta(days=5)), "admin@siol.com"
    )
    completado = mantenimiento_service.crear_mantenimiento(
        db, _mantenimiento(fecha=HOY + timedelta(days=2)), "admin@siol.com"
    )
    mantenimiento_service.completar_mantenimiento(
        db, completado["id"], CompletarMantenimientoRequest(), "admin@siol.com"
    )

    fila = mantenimiento_service.estado_flota(db)[0]

    assert fila["mantenimientos_abiertos"] == 1
    assert fila["proximo_mantenimiento"] == HOY + timedelta(days=5)


# ---------------------------------------------------------------------------
# 7b. Umbrales 30/15/7, licencias, ficha y marca "no apto"
# ---------------------------------------------------------------------------


def test_niveles_de_alerta_30_15_7():
    """Cada umbral tiene su severidad y un vencido siempre es ALTA."""

    assert mantenimiento_service.nivel_alerta_vencimiento(30) == ("BAJA", 30)
    assert mantenimiento_service.nivel_alerta_vencimiento(25) == ("BAJA", 30)
    assert mantenimiento_service.nivel_alerta_vencimiento(15) == ("MEDIA", 15)
    assert mantenimiento_service.nivel_alerta_vencimiento(10) == ("MEDIA", 15)
    assert mantenimiento_service.nivel_alerta_vencimiento(7) == ("ALTA", 7)
    assert mantenimiento_service.nivel_alerta_vencimiento(1) == ("ALTA", 7)
    assert mantenimiento_service.nivel_alerta_vencimiento(-2) == ("ALTA", None)


def test_alerta_documento_en_umbral_30_es_baja(db):
    """A 25 dias del vencimiento la alerta es BAJA con umbral 30."""

    _vehiculo(db)
    mantenimiento_service.crear_documento(
        db,
        _documento(
            emision=HOY - timedelta(days=300),
            vencimiento=HOY + timedelta(days=25),
        ),
        "admin@siol.com",
    )

    avisos = [
        aviso
        for aviso in mantenimiento_service.alertas(db)
        if aviso["tipo"] == "DOCUMENTO"
    ]

    assert len(avisos) == 1
    assert avisos[0]["severidad"] == "BAJA"
    assert avisos[0]["umbral"] == 30


def test_alerta_documento_en_umbral_7_es_alta(db):
    """A 5 dias del vencimiento la alerta ya es ALTA con umbral 7."""

    _vehiculo(db)
    mantenimiento_service.crear_documento(
        db,
        _documento(
            emision=HOY - timedelta(days=300),
            vencimiento=HOY + timedelta(days=5),
        ),
        "admin@siol.com",
    )

    avisos = [
        aviso
        for aviso in mantenimiento_service.alertas(db)
        if aviso["tipo"] == "DOCUMENTO"
    ]

    assert len(avisos) == 1
    assert avisos[0]["severidad"] == "ALTA"
    assert avisos[0]["umbral"] == 7


def test_renovacion_reemplaza_documento_vencido(db):
    """Si el SOAT se renovo, el registro viejo queda como historial y no veta."""

    _vehiculo(db)
    mantenimiento_service.crear_documento(
        db,
        _documento(
            numero="SOAT-OLD",
            emision=HOY - timedelta(days=400),
            vencimiento=HOY - timedelta(days=30),
        ),
        "admin@siol.com",
    )
    mantenimiento_service.crear_documento(
        db, _documento(numero="SOAT-NEW"), "admin@siol.com"
    )
    mantenimiento_service.crear_documento(
        db,
        _documento(
            tipo=TipoDocumentoEnum.REVISION_TECNICA,
            numero="RT-001",
            vencimiento=HOY + timedelta(days=400),
        ),
        "admin@siol.com",
    )

    fila = mantenimiento_service.estado_flota(db)[0]
    ficha = mantenimiento_service.ficha_vehiculo(db, "ABC-123")
    avisos = [
        aviso
        for aviso in mantenimiento_service.alertas(db)
        if aviso["tipo"] == "DOCUMENTO"
    ]

    assert fila["estado_general"] == "AL_DIA"
    assert fila["documentos_total"] == 2
    assert fila["documentos_vencidos"] == 0
    assert fila["proximo_vencimiento"] == HOY + timedelta(days=365)
    assert fila["apto_para_salir"] is True
    assert len(ficha["documentos"]) == 3  # el historial se conserva
    assert ficha["documentos_total"] == 2  # los contadores usan la renovacion
    assert avisos == []


def test_resumen_ignora_renovaciones_anteriores(db):
    """El resumen cuenta el documento actual de cada tipo, no el historial."""

    _vehiculo(db)
    mantenimiento_service.crear_documento(
        db,
        _documento(
            numero="SOAT-OLD",
            emision=HOY - timedelta(days=400),
            vencimiento=HOY - timedelta(days=30),
        ),
        "admin@siol.com",
    )
    mantenimiento_service.crear_documento(
        db, _documento(numero="SOAT-NEW"), "admin@siol.com"
    )

    resultado = mantenimiento_service.resumen(db)

    assert resultado["documentos_total"] == 1
    assert resultado["documentos_vigentes"] == 1
    assert resultado["documentos_vencidos"] == 0
    assert resultado["documentos_por_tipo"] == {"SOAT": 1}


def test_licencias_no_se_mezclan_con_alertas_de_almacen(db):
    """Las licencias solo aparecen si se piden explicitamente (rol admin)."""

    _conductor(db, vencimiento=HOY + timedelta(days=10))

    sin_licencias = [
        aviso
        for aviso in mantenimiento_service.alertas(db)
        if aviso["tipo"] == "LICENCIA"
    ]
    con_licencias = [
        aviso
        for aviso in mantenimiento_service.alertas(db, incluir_licencias=True)
        if aviso["tipo"] == "LICENCIA"
    ]

    assert sin_licencias == []
    assert len(con_licencias) == 1
    assert con_licencias[0]["conductor"] == "Ana Torres"
    assert con_licencias[0]["placa"] is None
    assert con_licencias[0]["severidad"] == "MEDIA"
    assert con_licencias[0]["umbral"] == 15


def test_alerta_licencia_vencida_es_alta(db):
    """Una licencia vencida genera una alerta ALTA sin umbral."""

    _conductor(db, vencimiento=HOY - timedelta(days=2))

    avisos = [
        aviso
        for aviso in mantenimiento_service.alertas(db, incluir_licencias=True)
        if aviso["tipo"] == "LICENCIA"
    ]

    assert len(avisos) == 1
    assert avisos[0]["severidad"] == "ALTA"
    assert avisos[0]["dias"] == -2
    assert avisos[0]["umbral"] is None


def test_listar_licencias_calcula_estado_y_nivel(db):
    """La licencia se lee del nucleo y se devuelve con su estado calculado."""

    _conductor(db, vencimiento=HOY + timedelta(days=10))

    fila = mantenimiento_service.listar_licencias(db)[0]

    assert fila["nombre"] == "Ana Torres"
    assert fila["licencia_numero"] == "Q12345678"
    assert fila["estado"] == EstadoDocumentoEnum.POR_VENCER.value
    assert fila["dias_para_vencer"] == 10
    assert fila["nivel_alerta"] == "MEDIA"
    assert fila["umbral"] == 15


def test_listar_licencias_sin_fecha_queda_sin_documento(db):
    """Un conductor sin vencimiento de licencia se reporta SIN_DOCUMENTO."""

    _conductor(db, vencimiento=None)

    fila = mantenimiento_service.listar_licencias(db)[0]

    assert fila["estado"] == EstadoDocumentoEnum.SIN_DOCUMENTO.value
    assert fila["dias_para_vencer"] is None
    assert fila["nivel_alerta"] is None


def test_resumen_cuenta_licencias_solo_si_se_piden(db):
    """El resumen del admin incluye las alertas de licencias; el de almacen no."""

    _conductor(db, vencimiento=HOY + timedelta(days=10))

    sin_licencias = mantenimiento_service.resumen(db)
    con_licencias = mantenimiento_service.resumen(db, incluir_licencias=True)

    assert sin_licencias["alertas_total"] == 0
    assert con_licencias["alertas_total"] == 1
    assert con_licencias["alertas_alta"] == 0


def test_ficha_vehiculo_junta_documentos_mantenimientos_y_costos(db):
    """La ficha de una unidad resume documentos, mantenimientos y costos."""

    _vehiculo(db)
    mantenimiento_service.crear_documento(db, _documento(), "admin@siol.com")
    mantenimiento_service.crear_documento(
        db,
        _documento(
            tipo=TipoDocumentoEnum.REVISION_TECNICA, numero="RT-001"
        ),
        "admin@siol.com",
    )
    mantenimiento_service.crear_mantenimiento(
        db,
        _mantenimiento(
            estado=EstadoMantenimientoEnum.COMPLETADO,
            fecha_ejecucion=HOY,
            kilometraje=1000,
            costo=100,
        ),
        "admin@siol.com",
    )
    mantenimiento_service.crear_mantenimiento(
        db,
        _mantenimiento(
            estado=EstadoMantenimientoEnum.COMPLETADO,
            fecha_ejecucion=HOY,
            kilometraje=1200,
            costo=100,
        ),
        "admin@siol.com",
    )

    ficha = mantenimiento_service.ficha_vehiculo(db, " abc-123 ")

    assert ficha["placa"] == "ABC-123"
    assert ficha["documentos_total"] == 2
    assert len(ficha["documentos"]) == 2
    assert len(ficha["mantenimientos"]) == 2
    assert ficha["estado_general"] == "AL_DIA"
    assert ficha["apto_para_salir"] is True
    assert ficha["motivos_no_apto"] == []
    assert ficha["costos"]["costo_total"] == 200.0
    assert ficha["costos"]["mantenimientos_completados"] == 2
    assert ficha["costos"]["costo_por_kilometro"] == 1.0
    assert ficha["odometro_actual"] == 1200


def test_ficha_vehiculo_inexistente_da_404(db):
    """Una placa que no existe devuelve 404, no una ficha vacia."""

    with pytest.raises(HTTPException) as error:
        mantenimiento_service.ficha_vehiculo(db, "ZZZ-999")

    assert error.value.status_code == 404


def test_no_apto_por_documento_vencido(db):
    """Un documento vencido marca la unidad como no apta para salir."""

    _vehiculo(db)
    mantenimiento_service.crear_documento(
        db,
        _documento(
            emision=HOY - timedelta(days=400),
            vencimiento=HOY - timedelta(days=1),
        ),
        "admin@siol.com",
    )
    mantenimiento_service.crear_documento(
        db,
        _documento(
            tipo=TipoDocumentoEnum.REVISION_TECNICA, numero="RT-001"
        ),
        "admin@siol.com",
    )

    fila = mantenimiento_service.estado_flota(db)[0]

    assert fila["apto_para_salir"] is False
    assert "SOAT vencido" in fila["motivos_no_apto"]


def test_no_apto_por_documento_obligatorio_faltante(db):
    """Si falta un documento obligatorio, la unidad tampoco es apta."""

    _vehiculo(db)
    mantenimiento_service.crear_documento(db, _documento(), "admin@siol.com")

    fila = mantenimiento_service.estado_flota(db)[0]

    assert fila["apto_para_salir"] is False
    assert "Falta REVISION_TECNICA" in fila["motivos_no_apto"]


# ---------------------------------------------------------------------------
# 8. Bandera de apagado del modulo
# ---------------------------------------------------------------------------


def test_router_apagado(monkeypatch):
    """Con la bandera en False el modulo no registra ninguna ruta."""

    monkeypatch.setattr(settings, "MODULO_MANTENIMIENTO_ENABLED", False)
    app_prueba = FastAPI()

    assert mantenimiento_router.incluir_router(app_prueba) is False
    assert not any(
        getattr(ruta, "path", "").startswith("/api/modulo-mantenimiento")
        for ruta in app_prueba.routes
    )


def test_router_encendido(monkeypatch):
    """Con la bandera en True el modulo expone /salud y sus rutas."""

    monkeypatch.setattr(settings, "MODULO_MANTENIMIENTO_ENABLED", True)
    app_prueba = FastAPI()

    assert mantenimiento_router.incluir_router(app_prueba) is True

    rutas = app_prueba.openapi().get("paths", {})
    assert "/api/modulo-mantenimiento/salud" in rutas
    assert "/api/modulo-mantenimiento/documentos" in rutas
    assert "/api/modulo-mantenimiento/mantenimientos" in rutas
    assert "/api/modulo-mantenimiento/alertas" in rutas
    assert "/api/modulo-mantenimiento/flota/{placa}" in rutas
    assert "/api/modulo-mantenimiento/licencias" in rutas