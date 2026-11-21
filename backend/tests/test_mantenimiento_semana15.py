# Pruebas de la semana 15 del modulo de mantenimiento (Idea 4).
# Usan SQLite en memoria y solo leen las tablas del nucleo.
from datetime import date, datetime, timedelta

import pytest
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
    DocumentoCreateRequest,
    MantenimientoCreateRequest,
    PreventivoCreateRequest,
    TipoDocumentoEnum,
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
    """Sesion SQLite en memoria compartida con los hilos del router ASGI."""

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


def _vehiculo(db, placa):
    """Crea una unidad activa de prueba. Recibe la sesion y la placa."""

    vehiculo = Vehiculo(placa=placa, marca="Toyota", estado="DISPONIBLE")
    db.add(vehiculo)
    db.commit()
    db.refresh(vehiculo)
    return vehiculo


def _documento(placa, tipo, vencimiento, numero):
    """Arma una peticion de documento con fechas coherentes."""

    return DocumentoCreateRequest(
        placa=placa,
        tipo_documento=tipo,
        numero=numero,
        entidad_emisora="La Positiva",
        fecha_emision=HOY - timedelta(days=365),
        fecha_vencimiento=vencimiento,
    )


def test_tablero_clasifica_las_unidades(db):
    """El tablero separa operativas, no aptas y unidades en taller."""

    _vehiculo(db, "ABC-100")
    mantenimiento_service.crear_documento(
        db, _documento("ABC-100", TipoDocumentoEnum.SOAT, HOY + timedelta(days=200), "S-100"), "admin@siol.com"
    )
    mantenimiento_service.crear_documento(
        db, _documento("ABC-100", TipoDocumentoEnum.REVISION_TECNICA, HOY + timedelta(days=200), "R-100"), "admin@siol.com"
    )

    _vehiculo(db, "ABC-200")
    mantenimiento_service.crear_documento(
        db, _documento("ABC-200", TipoDocumentoEnum.SOAT, HOY - timedelta(days=5), "S-200"), "admin@siol.com"
    )

    _vehiculo(db, "ABC-300")
    mantenimiento_service.crear_mantenimiento(
        db,
        MantenimientoCreateRequest(
            placa="ABC-300",
            descripcion="Revision en taller",
            fecha_programada=HOY + timedelta(days=2),
        ),
        "admin@siol.com",
    )

    tablero = mantenimiento_service.tablero(db)
    assert tablero["total_vehiculos"] == 3
    assert tablero["operativos"] == 1
    assert tablero["no_aptos"] == 2
    assert tablero["en_taller"] == 1
    assert tablero["mantenimientos_abiertos"] == 1
    assert tablero["fecha"] == HOY


def test_calendario_reune_los_tres_origenes(db):
    """El calendario junta documentos, mantenimientos y preventivos por fecha."""

    _vehiculo(db, "ABC-100")
    mantenimiento_service.crear_documento(
        db, _documento("ABC-100", TipoDocumentoEnum.SOAT, HOY + timedelta(days=10), "S-101"), "admin@siol.com"
    )
    mantenimiento_service.crear_mantenimiento(
        db,
        MantenimientoCreateRequest(
            placa="ABC-100",
            descripcion="Cambio de aceite",
            fecha_programada=HOY + timedelta(days=5),
        ),
        "admin@siol.com",
    )
    mantenimiento_service.crear_preventivo(
        db,
        PreventivoCreateRequest(
            placa="ABC-100",
            categoria="FRENOS",
            descripcion="Revision de frenos",
            intervalo_km=1000,
            intervalo_dias=20,
            fecha_base=HOY,
        ),
        "admin@siol.com",
    )

    eventos = mantenimiento_service.calendario(
        db, desde=HOY, hasta=HOY + timedelta(days=30)
    )
    tipos = [evento["tipo"] for evento in eventos]
    assert set(tipos) == {"DOCUMENTO", "MANTENIMIENTO", "PREVENTIVO"}
    assert [evento["fecha"] for evento in eventos] == sorted(
        evento["fecha"] for evento in eventos
    )
    assert all(evento["placa"] == "ABC-100" for evento in eventos)


def test_calendario_rechaza_rango_invertido(db):
    """La fecha inicial no puede ser posterior a la final."""

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as error:
        mantenimiento_service.calendario(
            db,
            desde=HOY + timedelta(days=10),
            hasta=HOY,
        )
    assert error.value.status_code == 422


def test_recordatorio_prepara_resumen_y_envia(db, monkeypatch):
    """El correo incluye el resumen de alertas y usa el destinatario pedido."""

    from app.services import correo_service

    llamados = []
    monkeypatch.setattr(
        correo_service,
        "enviar_simple",
        lambda destino, asunto, cuerpo: llamados.append((destino, asunto, cuerpo)) or True,
    )
    _vehiculo(db, "ABC-100")
    mantenimiento_service.crear_documento(
        db,
        _documento("ABC-100", TipoDocumentoEnum.SOAT, HOY - timedelta(days=3), "S-102"),
        "admin@siol.com",
    )

    resultado = mantenimiento_service.enviar_recordatorio(
        db, destino="jefe@siol.com", hoy=HOY
    )
    assert resultado["enviado"] is True
    assert resultado["destino"] == "jefe@siol.com"
    assert resultado["alertas"] >= 1
    assert len(llamados) == 1
    assert "Recordatorio de mantenimiento" in llamados[0][1]
    assert "SOAT" in llamados[0][2]


def test_ficha_pdf_se_genera_sin_librerias(db):
    """La ficha produce un PDF valido con su nombre de archivo."""

    _vehiculo(db, "ABC-777")
    contenido, nombre = mantenimiento_service.ficha_pdf(db, "ABC-777")
    assert contenido.startswith(b"%PDF-1.4")
    assert contenido.rstrip().endswith(b"%%EOF")
    assert b"/Type /Page" in contenido
    assert nombre == "ficha_ABC-777.pdf"


def test_excel_reporte_incluye_hojas_y_respeta_filtros(db):
    """El reporte abre con openpyxl y filtra por placa."""

    from io import BytesIO

    from openpyxl import load_workbook

    from app.schemas.mantenimiento import (
        CargaCombustibleCreateRequest,
        TipoCombustibleEnum,
    )

    _vehiculo(db, "ABC-100")
    _vehiculo(db, "ABC-200")
    mantenimiento_service.crear_documento(
        db,
        _documento("ABC-100", TipoDocumentoEnum.SOAT, HOY + timedelta(days=100), "S-103"),
        "admin@siol.com",
    )
    mantenimiento_service.crear_carga(
        db,
        CargaCombustibleCreateRequest(
            placa="ABC-100",
            fecha=HOY,
            tipo_combustible=TipoCombustibleEnum.DIESEL,
            galones=10,
            monto=100,
            odometro=1000,
        ),
        "admin@siol.com",
    )

    ficha, nombre_pdf = mantenimiento_service.ficha_pdf(db, "ABC-100")
    assert ficha.startswith(b"%PDF-") and nombre_pdf.endswith(".pdf")

    contenido, nombre = mantenimiento_service.excel_reporte(
        db, placa="ABC-100", hoy=HOY
    )
    libro = load_workbook(BytesIO(contenido))
    assert nombre == f"mantenimiento_ABC-100_{HOY}.xlsx"
    assert set(libro.sheetnames) == {
        "Resumen", "Flota", "Documentos", "Mantenimientos", "Preventivos", "Combustible"
    }
    filas_flota = list(libro["Flota"].values)
    assert len(filas_flota) == 2  # encabezado + una unidad filtrada
    assert filas_flota[1][0] == "ABC-100"
    assert len(list(libro["Combustible"].values)) == 2


def test_archivo_privado_acepta_pdf_y_rechaza_ruta(db, tmp_path, monkeypatch):
    """El adjunto se guarda con nombre aleatorio y solo se lee por su clave."""

    from fastapi import HTTPException

    from app.core.config import settings

    monkeypatch.setattr(settings, "UPLOADS_DIR", str(tmp_path))
    monkeypatch.setattr(settings, "ALMACENAMIENTO", "local")
    _vehiculo(db, "ABC-100")
    documento = mantenimiento_service.crear_documento(
        db,
        _documento("ABC-100", TipoDocumentoEnum.SOAT, HOY + timedelta(days=100), "S-104"),
        "admin@siol.com",
    )

    resultado = mantenimiento_service.guardar_archivo_documento(
        db, documento["id"], b"%PDF-1.4\ncontenido de prueba", "soat.pdf", "admin@siol.com"
    )
    assert resultado["tipo"] == ".pdf"
    assert resultado["archivo_url"].startswith("/media/privado/mantenimiento/")
    clave = resultado["archivo_url"][len("/media/") :]
    contenido, tipo = mantenimiento_service.leer_archivo_privado(clave)
    assert contenido.startswith(b"%PDF-")
    assert tipo == "application/pdf"

    with pytest.raises(HTTPException) as error:
        mantenimiento_service.leer_archivo_privado("evidencias/pod.jpg")
    assert error.value.status_code == 404

    with pytest.raises(HTTPException) as error:
        mantenimiento_service.guardar_archivo_documento(
            db, documento["id"], b"no soy un pdf", "soat.pdf", "admin@siol.com"
        )
    assert error.value.status_code == 400


def test_endpoints_semana15_responden(db, tmp_path, monkeypatch):
    """Los endpoints nuevos devuelven datos, PDF, Excel y archivos privados."""

    import asyncio
    from types import SimpleNamespace

    import httpx
    from fastapi import FastAPI

    from app.api import mantenimiento as mantenimiento_api
    from app.api.deps import get_current_admin, get_current_almacen
    from app.core.config import settings
    from app.db.database import get_db

    monkeypatch.setattr(settings, "UPLOADS_DIR", str(tmp_path))
    monkeypatch.setattr(settings, "ALMACENAMIENTO", "local")
    _vehiculo(db, "ABC-100")
    documento = mantenimiento_service.crear_documento(
        db,
        _documento("ABC-100", TipoDocumentoEnum.SOAT, HOY - timedelta(days=2), "S-105"),
        "admin@siol.com",
    )

    aplicacion = FastAPI()
    aplicacion.include_router(
        mantenimiento_api.router, prefix="/api/modulo-mantenimiento"
    )
    usuario = SimpleNamespace(correo="admin@siol.com", rol="admin")
    aplicacion.dependency_overrides[get_db] = lambda: db
    aplicacion.dependency_overrides[get_current_admin] = lambda: usuario
    aplicacion.dependency_overrides[get_current_almacen] = lambda: usuario
    base = "/api/modulo-mantenimiento"

    async def consultar():
        transporte = httpx.ASGITransport(app=aplicacion)
        async with httpx.AsyncClient(
            transport=transporte, base_url="http://prueba"
        ) as cliente:
            tablero = await cliente.get(f"{base}/tablero")
            assert tablero.status_code == 200
            assert tablero.json()["total_vehiculos"] == 1

            calendario = await cliente.get(f"{base}/calendario")
            assert calendario.status_code == 200
            assert isinstance(calendario.json(), list)

            recordatorio = await cliente.post(
                f"{base}/recordatorio", json={"destino": "admin@siol.com"}
            )
            assert recordatorio.status_code == 200
            assert "enviado" in recordatorio.json()

            pdf = await cliente.get(f"{base}/flota/ABC-100/pdf")
            assert pdf.status_code == 200
            assert pdf.content.startswith(b"%PDF-")
            assert "attachment" in pdf.headers["content-disposition"]

            excel = await cliente.get(f"{base}/reporte/excel?placa=ABC-100")
            assert excel.status_code == 200
            assert excel.content.startswith(b"PK")

            subida = await cliente.post(
                f"{base}/documentos/{documento['id']}/archivo",
                files={"file": ("soat.pdf", b"%PDF-1.4\ncontenido", "application/pdf")},
            )
            assert subida.status_code == 201
            clave = subida.json()["archivo_url"].removeprefix("/media/")
            descarga = await cliente.get(f"{base}/archivos/{clave}")
            assert descarga.status_code == 200
            assert descarga.content.startswith(b"%PDF-")

    asyncio.run(consultar())
