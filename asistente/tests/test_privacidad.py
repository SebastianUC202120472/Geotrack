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
