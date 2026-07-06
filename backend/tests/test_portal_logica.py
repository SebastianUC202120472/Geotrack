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


def test_limitador_no_crece_por_clave_al_reusarla():
    # Una clave reusada tras expirar su ventana no acumula marcas viejas (se purgan).
    reloj = {"t": 1000.0}
    lim = _Limitador(lambda: reloj["t"])
    assert lim.permitir("ip1:/x", maximo=1, ventana_seg=10) is True
    reloj["t"] += 11          # expira la ventana
    assert lim.permitir("ip1:/x", maximo=1, ventana_seg=10) is True
    assert len(lim._eventos["ip1:/x"]) == 1   # solo la marca nueva, sin basura acumulada


def test_limitador_topa_numero_de_claves():
    reloj = {"t": 0.0}
    lim = _Limitador(lambda: reloj["t"], max_claves=5)
    for i in range(50):
        reloj["t"] += 0.001
        lim.permitir(f"ip{i}:/x", maximo=10, ventana_seg=3600)
    assert len(lim._eventos) <= 5


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


# --- Gates de autorizacion (frontera de seguridad): se llaman las dependencias
#     directamente pasando una credencial Bearer simulada. ---
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from app.core.portal_token import requiere_token_persona, requiere_token_empresa


def _cred(token):
    """Arma una credencial Bearer simulada. Recibe el token (o None)."""
    if token is None:
        return None
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def test_token_persona_no_sirve_para_otro_pedido():
    tok = crear_token_persona("PD-1")
    with pytest.raises(HTTPException) as e:
        requiere_token_persona("PD-2", _cred(tok))
    assert e.value.status_code == 403


def test_token_persona_valido_devuelve_codigo():
    tok = crear_token_persona("PD-1")
    assert requiere_token_persona("PD-1", _cred(tok)) == "PD-1"


def test_token_persona_acepta_codigo_en_minusculas():
    tok = crear_token_persona("PD-1")   # sub siempre en mayusculas
    assert requiere_token_persona("pd-1", _cred(tok)) == "PD-1"


def test_token_persona_no_pasa_como_empresa():
    tok = crear_token_persona("PD-1")
    with pytest.raises(HTTPException) as e:
        requiere_token_empresa(_cred(tok))
    assert e.value.status_code == 401


def test_token_empresa_valido_devuelve_codigo_acceso():
    tok = crear_token_empresa("RIPLEY-24")
    assert requiere_token_empresa(_cred(tok)) == "RIPLEY-24"


def test_sin_bearer_da_401():
    with pytest.raises(HTTPException) as e:
        requiere_token_empresa(_cred(None))
    assert e.value.status_code == 401


# --- Tests de verificacion (OTP + DNI + bloqueos) ---
from app.services.verificacion_portal_service import gen_otp, evaluar_intento


def test_gen_otp_seis_digitos():
    o = gen_otp()
    assert len(o) == 6 and o.isdigit()


def test_evaluar_intento_bloquea_al_tercero():
    # (intentos_previos, exito, limite, bloqueo_seg) -> dict de resultado
    r1 = evaluar_intento(0, exito=False, limite=3, bloqueo_seg=30)
    assert r1["bloquear"] is False and r1["intentos_restantes"] == 2
    r2 = evaluar_intento(2, exito=False, limite=3, bloqueo_seg=30)
    assert r2["bloquear"] is True and r2["bloqueo_seg"] == 30
    r3 = evaluar_intento(1, exito=True, limite=3, bloqueo_seg=30)
    assert r3["ok"] is True


# --- Tests del servicio de portal (traducir eventos, resumen, detalle) ---
from datetime import datetime
from app.services.portal_service import traducir_eventos


class _H:
    def __init__(self, estado, fecha):
        self.estado_nuevo, self.fecha_utc = estado, fecha


def test_traducir_eventos_marca_entregado_ok():
    evs = traducir_eventos([
        _H("LISTO_PARA_ENVIO", datetime(2026, 7, 5, 9, 0)),
        _H("EN_RUTA", datetime(2026, 7, 5, 13, 0)),
        _H("ENTREGADO", datetime(2026, 7, 5, 14, 30)),
    ])
    assert evs[-1]["ok"] is True
    assert all("h" in e and "t" in e for e in evs)


def test_traducir_eventos_ultimo_en_ruta_es_vivo():
    evs = traducir_eventos([
        _H("LISTO_PARA_ENVIO", datetime(2026, 7, 5, 9, 0)),
        _H("EN_RUTA", datetime(2026, 7, 5, 13, 0)),
    ])
    assert evs[-1].get("vivo") is True


def test_traducir_eventos_fallido_es_alerta():
    evs = traducir_eventos([
        _H("EN_RUTA", datetime(2026, 7, 5, 13, 0)),
        _H("FALLIDO", datetime(2026, 7, 5, 16, 30)),
    ])
    assert evs[-1].get("alerta") is True


# --- Tests del repositorio de reclamos ---
from app.repositories.reclamo_repository import formato_codigo


def test_formato_codigo_lr():
    assert formato_codigo(2026, 7) == "LR-2026-0007"
    assert formato_codigo(2026, 1234) == "LR-2026-1234"


# --- Test del enmascarado de codigo (landing publico) ---
from app.services.enmascarado import mask_codigo


def test_mask_codigo():
    assert mask_codigo("PD-2481") == "PD-2••1"
    assert mask_codigo("PD-150") == "PD-1•0"
    assert mask_codigo("PD-15") == "PD-1•"
    assert mask_codigo("") == ""


def test_traducir_eventos_no_expone_estado_interno_crudo():
    # Un estado no catalogado NO debe salir crudo por el endpoint publico.
    evs = traducir_eventos([_H("ESTADO_INTERNO_RARO", datetime(2026, 7, 6, 10, 0))])
    assert evs[0]["t"] == "Actualizacion del envio"
    evs2 = traducir_eventos([_H("GEOCODIFICACION_FALLIDA", datetime(2026, 7, 6, 10, 0))])
    assert evs2[0]["t"] == "Verificando direccion de entrega"
