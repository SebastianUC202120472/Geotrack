# Respaldo del servidor: las tablas Markdown que escriba el modelo se quitan del texto.
from app.db.database import SessionLocal
from app.main import app
from app.models import Mensaje
from app.services.privacidad import FiltroTablas, es_fila_tabla, quitar_tablas
from tests.conftest import CadenaFalsa, cabecera, eventos_sse, llamada

RESPUESTA_CON_TABLA = (
    "Hay **12 pedidos fallidos**; el motivo más común es *cliente ausente*.\n"
    "\n"
    "| Código | Motivo de fallo |\n"
    "|---|:---:|\n"
    "| PD-001 | Cliente ausente |\n"
    "| PD-002 | Dirección incorrecta |\n"
    "\n"
    "Revisa la tabla de abajo para el detalle."
)
SIN_TABLA = (
    "Hay **12 pedidos fallidos**; el motivo más común es *cliente ausente*.\n"
    "\n"
    "Revisa la tabla de abajo para el detalle."
)


def _por_partes(texto: str, tam: int) -> str:
    """Pasa el texto por el filtro en trozos de tam caracteres. Recibe texto y tamaño."""
    filtro = FiltroTablas()
    salida = "".join(filtro.agregar(texto[i:i + tam]) for i in range(0, len(texto), tam))
    return salida + filtro.cerrar()


def test_quita_la_tabla_y_conserva_el_resumen():
    """La tabla sale del texto; el resumen y la frase final quedan igual."""
    assert quitar_tablas(RESPUESTA_CON_TABLA) == SIN_TABLA


def test_quita_la_tabla_aunque_llegue_partida():
    """En el streaming la tabla puede llegar de a un caracter o en trozos que cortan las filas."""
    for tam in (1, 2, 3, 7, 50, 1000):
        assert _por_partes(RESPUESTA_CON_TABLA, tam) == SIN_TABLA, tam


def test_tabla_sin_barras_externas_y_al_final_sin_salto():
    """Separador sin | inicial ('---|---') y una tabla que termina el texto sin salto de linea."""
    texto = "Resumen corto.\n| A | B |\n---|---\n| 1 | 2 |"
    assert _por_partes(texto, 4) == "Resumen corto.\n"


def test_no_toca_texto_normal_listas_ni_barras_sueltas():
    """Listas, negritas, una raya '---' y un '|' dentro de una frase no son tablas."""
    texto = "- Uno\n- **Dos**\n---\nRuta A | Ruta B tienen avance.\n1. Tres"
    assert _por_partes(texto, 1) == texto
    assert not es_fila_tabla("---") and not es_fila_tabla("Ruta A | Ruta B")
    assert es_fila_tabla("| a | b |") and es_fila_tabla(":--|--:")


def test_texto_normal_no_se_retiene():
    """Una linea que no empieza como tabla se entrega en cuanto se sabe (no espera el salto)."""
    filtro = FiltroTablas()
    assert filtro.agregar("Hoy van ") == "Hoy van "
    assert filtro.agregar("5 entregados") == "5 entregados"
    assert filtro.agregar("\n|") == "\n"   # el '|' se retiene hasta ver la linea completa
    assert filtro.agregar(" a | b |\nFin") == "Fin"
    assert filtro.quito_tabla


def test_chat_no_muestra_ni_guarda_la_tabla_del_modelo(cliente, nucleo):
    """Flujo completo: el modelo escribe una tabla; el usuario ve el resumen y la tabla del servidor."""
    app.state.cadena = CadenaFalsa([
        {"llamadas": [llamada("buscar_pedidos", {"estado": "FALLIDO", "presentar": "tabla"})]},
        {"texto": [RESPUESTA_CON_TABLA[i:i + 9] for i in range(0, len(RESPUESTA_CON_TABLA), 9)]},
    ])
    r = cliente.post("/api/asistente/chat", json={"mensaje": "¿qué pedidos fallaron y por qué?"}, headers=cabecera("tok-admin"))
    eventos = eventos_sse(r.text)
    texto = "".join(e["texto"] for e in eventos if e["tipo"] == "texto")
    assert texto == SIN_TABLA
    assert any(e["tipo"] == "bloque" and e["bloque"]["tipo"] == "tabla" for e in eventos)
    fin = next(e for e in eventos if e["tipo"] == "fin")
    with SessionLocal() as db:
        assert db.get(Mensaje, fin["mensaje_id"]).contenido == SIN_TABLA
