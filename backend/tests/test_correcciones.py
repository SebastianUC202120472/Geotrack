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
