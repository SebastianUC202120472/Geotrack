from jose import jwt as _jwt
from app.services.estado_portal import mapear_estado, progreso
from app.services.enmascarado import mask_telefono, mask_nombre, mask_direccion_corta
from app.core.rate_limit import _Limitador
from app.core.portal_token import crear_token_persona, crear_token_empresa
from app.core.config import settings


def test_mapeo_estados_pipeline_a_portal():
    assert mapear_estado("EN_RUTA") == "EN_RUTA"
    assert mapear_estado("ENTREGADO") == "ENTREGADO"
    assert mapear_estado("OBSERVADO") == "OBSERVADO"
    assert mapear_estado("FALLIDO") == "REPROGRAMADO"
    assert mapear_estado("CANCELADO") == "CANCELADO"
    for e in ("POR_RECOGER", "LISTO_PARA_ENVIO", "ASIGNADO"):
        assert mapear_estado(e) == "POR_SALIR"
    # desconocido -> POR_SALIR (nunca expone un estado interno raro)
    assert mapear_estado("LO_QUE_SEA") == "POR_SALIR"


def test_progreso_en_ruta_usa_secuencia():
    p = progreso("EN_RUTA", secuencia=12, total=28)
    assert p["paso"] == 2
    assert p["pct"] == "43%"   # round(12/28*100) = 43
    assert p["van"] == "43%"


def test_progreso_en_ruta_sin_secuencia_usa_fallback():
    p = progreso("EN_RUTA", secuencia=None, total=None)
    assert p["paso"] == 2
    assert p["pct"] == "50%"


def test_progreso_entregado_full():
    p = progreso("ENTREGADO", secuencia=None, total=None)
    assert p["paso"] == 3
    assert p["pct"] == "100%"


def test_mask_telefono():
    assert mask_telefono("+51 999 000 321") == "+51 9** *** *21"
    assert mask_telefono("") == ""


def test_mask_nombre():
    assert mask_nombre("Roberto Paredes") == "Robe•••"
    assert mask_nombre("Ana") == "Ana•••"


def test_mask_direccion_corta():
    assert mask_direccion_corta("Av. Brasil 1120") == "Av. ••• •••"


def test_limitador_permite_hasta_maximo_y_bloquea():
    reloj = {"t": 1000.0}
    lim = _Limitador(lambda: reloj["t"])
    for _ in range(3):
        assert lim.permitir("ip:/x", maximo=3, ventana_seg=60) is True
    assert lim.permitir("ip:/x", maximo=3, ventana_seg=60) is False
    # tras la ventana, se vuelve a permitir
    reloj["t"] += 61
    assert lim.permitir("ip:/x", maximo=3, ventana_seg=60) is True


def test_token_persona_lleva_scope_y_sub():
    tok = crear_token_persona("PD-2481")
    p = _jwt.decode(tok, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert p["scope"] == "portal_persona"
    assert p["sub"] == "PD-2481"


def test_token_empresa_lleva_scope():
    tok = crear_token_empresa("RIPLEY-24")
    p = _jwt.decode(tok, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert p["scope"] == "portal_empresa"
    assert p["sub"] == "RIPLEY-24"
