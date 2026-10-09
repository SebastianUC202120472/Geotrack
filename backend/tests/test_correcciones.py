# Pruebas de las correcciones del Excel de tareas (logica pura, sin base de datos).
from datetime import date, timedelta

import pytest

from app.schemas.cliente import normalizar_ruc, digito_ruc_valido, normalizar_razon_social
from app.schemas.conductor import validar_licencia, ConductorCreate
from app.services.verificacion_portal_service import segundos_de_bloqueo, ESCALONES_BLOQUEO_SEG


# --- C03-03: licencia de conducir ---

def test_licencia_se_normaliza():
    """La licencia acepta minusculas, espacios y guiones y se guarda limpia."""
    assert validar_licencia("q-1234 5678") == "Q12345678"


def test_licencia_mal_formada_se_rechaza():
    """Una licencia sin la letra inicial o con menos digitos no pasa."""
    with pytest.raises(ValueError):
        validar_licencia("12345678")


def test_alta_con_licencia_vencida_se_rechaza():
    """No se puede dar de alta a un conductor con la licencia vencida."""
    with pytest.raises(ValueError):
        ConductorCreate(correo="a@b.pe", contrasena="Clave12345!", nombre="Ana Pérez",
                        licencia_numero="Q12345678", licencia_vencimiento=date.today() - timedelta(days=2))


# --- C07-01: RUC y razon social ---

def test_ruc_valido_de_empresa_real():
    """Un RUC real de SUNAT cumple formato y digito verificador."""
    assert normalizar_ruc(" 20100128056 ") == "20100128056"
    assert digito_ruc_valido("20100128056")


def test_ruc_con_digito_errado():
    """Si se cambia el ultimo digito, el verificador ya no coincide."""
    assert not digito_ruc_valido("20100128057")


@pytest.mark.parametrize("ruc", ["2010012805", "201001280561", "30100128056", "20A00128056"])
def test_ruc_mal_formado(ruc):
    """Largo distinto de 11, prefijo invalido o letras: se rechaza."""
    with pytest.raises(ValueError):
        normalizar_ruc(ruc)


def test_razon_social_corta_se_rechaza():
    """La razon social exige al menos 3 caracteres utiles."""
    with pytest.raises(ValueError):
        normalizar_razon_social("  A ")
    assert normalizar_razon_social("  Saga   Falabella ") == "Saga Falabella"


# --- C42-01: bloqueo progresivo ---

def test_primer_bloqueo_usa_el_base():
    """El primer bloqueo dura lo de siempre (30 s DNI / 45 s OTP)."""
    assert segundos_de_bloqueo(30, 0) == 30


def test_bloqueos_seguidos_se_alargan_hasta_el_tope():
    """Cada bloqueo seguido dura mas y nunca pasa del ultimo escalon."""
    duraciones = [segundos_de_bloqueo(30, n) for n in range(8)]
    assert duraciones == sorted(duraciones)
    assert duraciones[-1] == ESCALONES_BLOQUEO_SEG[-1]


# --- F3: solicitudes de recojo ---
from fastapi import HTTPException  # noqa: E402
from app.models.solicitud_recojo import ESTADOS_GESTIONADOS  # noqa: E402
from app.schemas.recojo import PedidoManualIn, SolicitudManualCreate, NoRealizadoRequest  # noqa: E402
from app.services.recojo_service import _exigir_filas_validas  # noqa: E402


def test_pedido_manual_exige_referencia_y_direccion():
    """Un pedido escrito a mano sin referencia o sin direccion no pasa (C11-02)."""
    with pytest.raises(ValueError):
        PedidoManualIn(referencia_externa="  ", direccion_destino="Av. Larco 100, Miraflores")
    p = PedidoManualIn(referencia_externa=" SF-1 ", direccion_destino="Av.  Larco 100,  Miraflores")
    assert p.referencia_externa == "SF-1" and p.direccion_destino == "Av. Larco 100, Miraflores"


def test_solicitud_manual_sin_pedidos_se_rechaza():
    """La solicitud manual necesita al menos un pedido."""
    with pytest.raises(ValueError):
        SolicitudManualCreate(cliente_id=1, pedidos=[])


def test_reintento_con_todo_duplicado_es_409():
    """Si todas las filas ya existian, el reintento responde 409 y no crea nada (C11-01)."""
    with pytest.raises(HTTPException) as e:
        _exigir_filas_validas([], ["Fila 1: el pedido SF-1 ya está registrado (PD-001)"], duplicadas=1)
    assert e.value.status_code == 409


def test_filas_invalidas_sin_duplicados_es_400():
    """Si no hay filas validas por datos faltantes, responde 400 con el motivo."""
    with pytest.raises(HTTPException) as e:
        _exigir_filas_validas([], ["Fila 1: falta direccion_destino"], duplicadas=0)
    assert e.value.status_code == 400 and "falta direccion_destino" in e.value.detail


def test_no_realizado_cuenta_como_gestionado_y_exige_motivo():
    """Un recojo no realizado ya no esta pendiente en la ruta y requiere motivo (C12-02)."""
    assert "NO_REALIZADO" in ESTADOS_GESTIONADOS
    with pytest.raises(ValueError):
        NoRealizadoRequest(motivo=" a ")
