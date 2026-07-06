from app.services.estado_portal import mapear_estado, progreso


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
