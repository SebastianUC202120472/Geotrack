import pytest
from fastapi import HTTPException

from app.services.portal_service import respuesta_login_empresa


def test_correo_enviado_nunca_expone_el_otp():
    """Si el correo salio, la respuesta no puede incluir el codigo por ningun motivo."""
    r = respuesta_login_empresa(enviado=True, otp="123456", correo_mask="lo***@ripley.com.pe", demo=True)
    assert r == {"enviado": True, "correoMask": "lo***@ripley.com.pe"}
    assert "otpDemo" not in r


def test_sin_correo_y_sin_modo_demo_sigue_siendo_503():
    """Con la bandera apagada se mantiene el comportamiento actual: 503, sin filtrar el codigo."""
    with pytest.raises(HTTPException) as e:
        respuesta_login_empresa(enviado=False, otp="123456", correo_mask="lo***@ripley.com.pe", demo=False)
    assert e.value.status_code == 503
    assert "123456" not in str(e.value.detail)


def test_sin_correo_y_con_modo_demo_devuelve_el_otp():
    """Con la bandera encendida el portal puede mostrar el codigo en pantalla."""
    r = respuesta_login_empresa(enviado=False, otp="654321", correo_mask="lo***@ripley.com.pe", demo=True)
    assert r["enviado"] is False
    assert r["otpDemo"] == "654321"
    assert r["correoMask"] == "lo***@ripley.com.pe"


def test_bandera_apagada_por_defecto():
    """PORTAL_OTP_DEMO no puede venir encendida de fabrica.
    Se mira el default declarado en el modelo y no una instancia: instanciar Settings
    leeria la variable de entorno del contenedor, que en desarrollo esta en true."""
    from app.core.config import Settings
    assert Settings.model_fields["PORTAL_OTP_DEMO"].default is False


def test_la_hora_del_portal_se_muestra_en_la_zona_de_la_operacion():
    """Una entrega de las 10:00 de Lima se guarda como 15:00 UTC; el cliente final debe
    leer 10:00, no la hora UTC cruda."""
    from datetime import datetime
    from app.services.portal_service import hora_local
    assert hora_local(datetime(2026, 9, 18, 15, 0)) == "10:00"
    assert hora_local(datetime(2026, 9, 19, 2, 6)) == "21:06"
    assert hora_local(None) == ""
