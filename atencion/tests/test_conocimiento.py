# Base de conocimiento: semilla valida y recuperacion BM25 en espanol e ingles.
import pytest

from app.conocimiento.buscador import IndiceConocimiento, normalizar, tokenizar
from app.conocimiento.semilla import articulos_semilla, aviso_privacidad


@pytest.fixture(scope="module")
def indice_semilla():
    """Indice armado con la semilla completa."""
    i = IndiceConocimiento()
    i.cargar(articulos_semilla())
    return i


def test_semilla_tiene_al_menos_30_preguntas_en_ambos_idiomas():
    """La semilla trae ~30 FAQ, cada una en espanol y en ingles, sin claves repetidas."""
    filas = articulos_semilla()
    es = {f["clave"] for f in filas if f["idioma"] == "es"}
    en = {f["clave"] for f in filas if f["idioma"] == "en"}
    assert len(es) >= 30
    assert es == en


def test_semilla_solo_enlaza_rutas_de_sava():
    """Ningun articulo semilla trae enlaces a otros dominios."""
    for f in articulos_semilla():
        assert "http" not in f["contenido"].lower()


def test_aviso_de_privacidad_en_ambos_idiomas():
    """El aviso tiene version y los mismos puntos en espanol e ingles."""
    aviso = aviso_privacidad()
    assert aviso["version"]
    assert len(aviso["es"]["puntos"]) == len(aviso["en"]["puntos"]) >= 6


def test_normalizar_quita_tildes_y_conserva_la_enie():
    """La normalizacion iguala tildes pero no confunde 'año' con 'ano'."""
    assert normalizar("Reprogramación AÑO") == "reprogramacion año"


def test_tokenizar_usa_raices_y_sinonimos():
    """'paquete' cuenta como 'pedido' y las variantes de un verbo comparten raiz."""
    assert tokenizar("mi paquete", "es") == ["pedido"]
    assert tokenizar("reprogramar", "es") == tokenizar("reprogramación", "es")


@pytest.mark.parametrize("pregunta,idioma,esperada", [
    ("¿llegan a Ventanilla?", "es", "zonas"),
    ("a que distritos reparten", "es", "cobertura"),
    ("oe mi paquete no llega", "es", "pedido-no-llega"),
    ("quiero reprogramar mi entrega", "es", "reprogramar"),
    ("cuanto cuesta el servicio", "es", "tarifas"),
    ("como presento un reclamo", "es", "libro-reclamaciones"),
    ("quiero que recojan mis envíos", "es", "recojo-tiendas"),
    ("por que me piden el dni", "es", "verificacion-dni"),
    ("trabajan los domingos?", "es", "dias-operacion"),
    ("numero de whatsapp", "es", "contacto"),
    ("where is my order?", "en", "rastrear-pedido"),
    ("do you deliver to Callao", "en", "cobertura"),
    ("how much does it cost", "en", "tarifas"),
    ("I want to reschedule my delivery", "en", "reprogramar"),
    ("how do I file a complaint", "en", "libro-reclamaciones"),
])
def test_recupera_el_articulo_correcto(indice_semilla, pregunta, idioma, esperada):
    """La pregunta trae el articulo esperado entre los 3 primeros."""
    claves = [r.clave for r in indice_semilla.buscar(pregunta, idioma, 3)]
    assert esperada in claves, claves


def test_si_no_hay_nada_en_el_idioma_prueba_el_otro(indice_semilla):
    """Una pregunta en ingles marcada como espanol igual encuentra el articulo en ingles."""
    resultados = indice_semilla.buscar("recipient buyer", "es", 3, minimo=1.0)
    assert resultados and resultados[0].idioma == "en"


def test_pregunta_ajena_no_trae_resultados_sobre_el_minimo(indice_semilla):
    """Algo que no tiene que ver con SAVA no supera el puntaje minimo."""
    assert indice_semilla.buscar("receta de ceviche con limón", "es", 3, minimo=1.0) == []
