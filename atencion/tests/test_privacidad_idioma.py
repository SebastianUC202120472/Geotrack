# Enmascarado de datos personales y deteccion de idioma.
import pytest

from app.services.idioma import detectar
from app.services.privacidad import enmascarar_texto


@pytest.mark.parametrize("texto,no_debe_quedar", [
    ("mi dni es 45678912", "45678912"),
    ("el dni termina en 4321", "4321"),
    ("last 4 digits of the ID: 9876", "9876"),
    ("llámame al 987 654 321", "987 654 321"),
    ("cel +51 912345678", "912345678"),
    ("my number is +1 415 555 0134", "415 555 0134"),
    ("escribe a juana.perez@correo.pe", "juana.perez@correo.pe"),
])
def test_oculta_datos_personales(texto, no_debe_quedar):
    """DNI, ultimos digitos, telefonos y correos no llegan ni al modelo ni a la base."""
    assert no_debe_quedar not in enmascarar_texto(texto)


def test_conserva_el_numero_publico_de_sava_y_los_codigos():
    """El WhatsApp publico de SAVA y un codigo de pedido no son datos personales."""
    texto = "Escribe al +51 922 507 593 sobre el pedido PD-000123"
    assert enmascarar_texto(texto) == texto


@pytest.mark.parametrize("texto,idioma", [
    ("oe, mi paquete no llega", "es"),
    ("¿dónde está mi pedido?", "es"),
    ("where is my order?", "en"),
    ("my package hasn't arrived yet", "en"),
    ("hola", "es"),
    ("hello", "en"),
    ("llegan a Ventanilla?", "es"),
    ("reparten los domingos?", "es"),
    ("do you deliver to Miraflores on Saturdays?", "en"),
])
def test_detecta_el_idioma(texto, idioma):
    """Detecta espanol o ingles en mensajes cortos y con jerga."""
    assert detectar(texto, "es" if idioma == "en" else "en") == idioma


def test_sin_senales_conserva_la_pista():
    """Un codigo suelto no cambia el idioma de la conversacion."""
    assert detectar("PD-000123", "en") == "en"


def test_seudonimos_ocultan_y_restituyen_solo_al_mismo_visitante():
    """Correo y telefono viajan como marcas; el valor real se recupera solo en el servidor."""
    from app.services.privacidad import Seudonimos
    from app.services.salida import FiltroSalida

    seud = Seudonimos()
    texto = seud.ocultar("escríbeme a ana@demo.pe o al 987 654 321; repito: ana@demo.pe")
    assert texto == "escríbeme a [CORREO_1] o al [TEL_1]; repito: [CORREO_1]"
    assert seud.valor("[CORREO_1]") == "ana@demo.pe" and seud.valor("[TEL_9]") is None
    filtro = FiltroSalida(["sava.pe"], seud.restituir)
    visible = filtro.agregar("Te escribiremos a [CORREO_1] pronto ") + filtro.cerrar()
    assert "ana@demo.pe" in visible and "[CORREO_1]" in filtro.texto_completo


def test_seudonimos_respetan_el_numero_publico_de_sava():
    """El WhatsApp de SAVA no se convierte en marca."""
    from app.services.privacidad import Seudonimos

    assert Seudonimos().ocultar("WhatsApp +51 922 507 593") == "WhatsApp +51 922 507 593"


@pytest.mark.parametrize("fragmentos,idioma,esperado", [
    (["Para la propuesta puedes usar las marcas ", "[CORREO_1] y ", "[TEL_1]. "], "es",
     "Para la propuesta puedes usar las marcas tu correo y tu teléfono. "),
    (["We will call ", "[TEL_2] soon."], "en", "We will call your phone number soon."),
    (["No guardamos [DNI oculto] ni ", "[dígitos ocultos]."], "es", "No guardamos el DNI ni los dígitos."),
    (["Escríbenos con [correo] o ", "[Teléfono_1]."], "es", "Escríbenos con tu correo o tu teléfono."),
])
def test_marcas_internas_nunca_llegan_al_visitante(fragmentos, idioma, esperado):
    """Una marca sin valor del visitante (o una inventada por el modelo) se cambia por palabras normales,
    aunque llegue partida entre fragmentos."""
    from app.services.privacidad import Seudonimos
    from app.services.salida import FiltroSalida

    filtro = FiltroSalida(["sava.pe"], Seudonimos().restituir, idioma=idioma)
    visible = "".join(filtro.agregar(f) for f in fragmentos) + filtro.cerrar()
    assert visible == esperado and "[" not in visible


def test_marcas_del_visitante_se_restituyen_y_las_demas_se_quitan():
    """La marca del propio visitante muestra su valor; la que no tiene valor no se muestra como marca."""
    from app.services.privacidad import Seudonimos
    from app.services.salida import FiltroSalida

    seud = Seudonimos()
    seud.ocultar("mi correo es ana@demo.pe")
    filtro = FiltroSalida(["sava.pe"], seud.restituir)
    visible = filtro.agregar("Anoté [CORREO_1]; falta [TEL_1] ") + filtro.cerrar()
    assert visible == "Anoté ana@demo.pe; falta tu teléfono "
    assert "[CORREO_1]" in filtro.texto_completo   # lo que se guarda sigue sin el dato real


def test_el_prompt_prohibe_mostrar_marcas_y_mezclar_idiomas():
    """Las instrucciones piden no escribir las marcas internas y responder en un solo idioma."""
    from app.ia.prompt import instrucciones_sistema

    texto = instrucciones_sistema("es")
    assert "NUNCA las escribas en tu respuesta" in texto
    assert "SOLO en español" in texto and "No mezcles idiomas" in texto
