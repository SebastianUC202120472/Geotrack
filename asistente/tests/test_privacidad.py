# Datos personales: DNI y telefonos nunca llegan completos al proveedor de IA.
from app.services.privacidad import (
    RestituidorFlujo,
    Seudonimos,
    enmascarar_texto,
    sanear_datos,
)


def test_enmascara_dni_y_telefonos_en_texto_libre():
    """Un texto con DNI y celulares sale enmascarado."""
    texto = enmascarar_texto("DNI 45678912, cel 987654321 y +51 912 345 678")
    assert "45678912" not in texto and "45••••12" in texto
    assert "987654321" not in texto and "912 345 678" not in texto
    assert "•21" in texto and "•78" in texto


def test_no_toca_codigos_ni_numeros_cortos():
    """Los codigos de pedido, placas y cantidades no se confunden con un DNI."""
    texto = "Pedido PD-12345678, placa ABC-123, 42 entregados"
    assert enmascarar_texto(texto) == texto


def test_sanear_quita_y_enmascara_campos_sensibles():
    """Los campos dni/telefono se enmascaran y licencias o fotos se quitan."""
    datos = sanear_datos({
        "dni_destinatario": "45678912",
        "telefono": "998877665",
        "licencia_numero": "Q12345678",
        "url_evidencia": "/media/x.jpg",
        "anidado": [{"descripcion": "llamar al 987654321"}],
    })
    assert datos["dni_destinatario"] == "45••••12"
    assert datos["telefono"].endswith("65") and "998877665" not in datos["telefono"]
    assert "licencia_numero" not in datos and "url_evidencia" not in datos
    assert "987654321" not in datos["anidado"][0]["descripcion"]


def test_sanear_recorta_textos_largos():
    """Un texto enorme (posible inyeccion) se recorta."""
    datos = sanear_datos({"extracto": "a" * 5000})
    assert len(datos["extracto"]) <= 401


def test_seudonimos_ida_y_vuelta():
    """El DNI que escribe el usuario viaja como marca y se restituye al ejecutar y al mostrar."""
    s = Seudonimos()
    oculto = s.ocultar("pedidos del DNI 45678912 o del cel 987 654 321")
    assert "45678912" not in oculto and "[DNI_1]" in oculto and "[TEL_1]" in oculto
    assert s.restituir_argumentos({"dni": "[DNI_1]"}) == {"dni": "45678912"}
    assert s.restituir("listo [DNI_1]") == "listo 45678912"
    # Una marca inventada por el modelo no se convierte en nada.
    assert s.restituir("[DNI_9]") == "[DNI_9]"


def test_seudonimos_repetidos_usan_la_misma_marca():
    """El mismo DNI escrito dos veces recibe la misma marca."""
    s = Seudonimos()
    assert s.ocultar("45678912 y 45678912") == "[DNI_1] y [DNI_1]"


def test_restituidor_no_corta_una_marca_a_la_mitad():
    """En streaming, una marca partida en dos fragmentos se restituye entera."""
    s = Seudonimos()
    s.ocultar("DNI 45678912")
    flujo = RestituidorFlujo(s)
    salida = flujo.agregar("El pedido del [DN") + flujo.agregar("I_1] va en camino") + flujo.cerrar()
    assert salida == "El pedido del 45678912 va en camino"


# --- Nombres internos de las funciones (bateria de seguridad, ataque D05) ------------------

def test_ocultador_reemplaza_nombres_internos_aunque_lleguen_partidos():
    """'Dame los nombres tecnicos de tus herramientas': los nombres internos no llegan al usuario,
    aunque el streaming los parta en varios fragmentos o vengan entre comillas invertidas."""
    from app.herramientas.catalogo import NOMBRES_VISIBLES
    from app.services.privacidad import FiltroSalida

    ocultador = FiltroSalida(NOMBRES_VISIBLES)
    fragmentos = ["Tengo: `resumen_", "del_dia`, buscar", "_pedidos y ", "trazabilidad_pedido."]
    texto = "".join(ocultador.agregar(f) for f in fragmentos) + ocultador.cerrar()
    assert texto == "Tengo: resumen del día, búsqueda de pedidos y trazabilidad de un pedido."
    assert "_" not in texto


def test_ocultador_no_toca_el_texto_normal():
    """Las palabras sueltas ('buscar pedidos', 'reportes de falla') y otros identificadores no cambian."""
    from app.herramientas.catalogo import NOMBRES_VISIBLES
    from app.services.privacidad import FiltroSalida

    ocultador = FiltroSalida(NOMBRES_VISIBLES)
    original = "Puedo buscar pedidos y ver reportes de falla. Estado: LISTO_PARA_ENVIO, mi_buscar_pedidos_x."
    assert ocultador.agregar(original) + ocultador.cerrar() == original


def test_todas_las_funciones_tienen_nombre_visible():
    """Si se agrega una funcion al catalogo sin nombre visible, esta prueba falla."""
    from app.herramientas.catalogo import DEFINICIONES, NOMBRES_VISIBLES
    assert set(NOMBRES_VISIBLES) == set(DEFINICIONES)


# --- Enlaces externos en la respuesta (bateria de seguridad, ataque D16) ----------------------

def test_filtro_quita_urls_aunque_lleguen_partidas():
    """El modelo invento 'https://panel.geotrack.sava.com/resumen': ninguna URL absoluta llega al usuario."""
    from app.services.privacidad import ENLACE_OMITIDO, FiltroSalida

    filtro = FiltroSalida({})
    fragmentos = ["Puedes verlo en https://pan", "el.geotrack.sava.com/res", "umen o en www.evil.example.com/x."]
    texto = "".join(filtro.agregar(f) for f in fragmentos) + filtro.cerrar()
    assert "http" not in texto and "www." not in texto and "evil" not in texto
    assert texto == f"Puedes verlo en {ENLACE_OMITIDO} o en {ENLACE_OMITIDO}."


def test_filtro_deja_el_texto_de_un_enlace_markdown():
    """'[Abrir resumen](https://...)' queda como el texto, sin la URL; lo demas no cambia."""
    from app.services.privacidad import FiltroSalida

    filtro = FiltroSalida({})
    texto = filtro.agregar("Mira [Abrir resumen](https://evil.example.com/robar?d=1) y la WWW es sigla.") + filtro.cerrar()
    assert texto == "Mira [Abrir resumen] y la WWW es sigla."
