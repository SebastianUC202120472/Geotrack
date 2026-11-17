# Genera los borradores para el gerente a partir de los MISMOS archivos que usa el servicio:
#   app/conocimiento/semilla.json           -> docs/faq_borrador.md
#   app/conocimiento/aviso_privacidad.json  -> docs/aviso_privacidad_borrador.md
# Asi lo que se valida y lo que responde el asistente nunca quedan desalineados.
# Uso (desde atencion/): python scripts/generar_borradores.py
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CONOCIMIENTO = RAIZ / "app" / "conocimiento"
DOCS = RAIZ / "docs"
DIAS_RETENCION = 30   # valor por defecto de ATENCION_RETENCION_DIAS


def _leer(nombre: str) -> dict:
    """Lee un JSON de la carpeta de conocimiento. Recibe el nombre del archivo."""
    return json.loads((CONOCIMIENTO / nombre).read_text(encoding="utf-8"))


def faq_markdown() -> str:
    """Arma el borrador de preguntas frecuentes en espanol e ingles. Sin input."""
    semilla = _leer("semilla.json")
    articulos = semilla["articulos"]
    por_validar = [a for a in articulos if a.get("por_validar")]
    lineas = [
        "# Borrador de preguntas frecuentes (ES/EN) del asistente de atención",
        "",
        f"**Estado:** borrador para validar por el gerente · **{len(articulos)} preguntas** en español e inglés · "
        f"**{len(por_validar)} con datos por confirmar** (marcadas con ⚠).",
        "",
        "Este documento se genera solo desde `app/conocimiento/semilla.json`, que es lo que el asistente carga "
        "la primera vez. Para corregir una respuesta, indíquelo aquí o edítela en el JSON. Desde la semana 15 "
        "también se podrá editar desde la pantalla de administración del panel.",
        "",
        "Fuente de los datos: textos de la landing (cobertura, servicio, contacto, reclamos) y comportamiento del "
        "portal (verificación por DNI, reprogramación, portal de empresas). Lo que **no** figura en el código "
        "(plazos de entrega, domingos, cantidad de intentos, horario de atención, procedimiento para cambiar "
        "la dirección) no se inventó: quedó redactado de forma prudente y marcado con ⚠.",
        "",
        "## Datos por confirmar",
        "",
    ]
    for a in por_validar:
        lineas.append(f"- **{a['es']['titulo']}** (`{a['clave']}`): {a['por_validar']}")
    categoria = None
    for n, a in enumerate(sorted(articulos, key=lambda x: x["categoria"]), start=1):
        if a["categoria"] != categoria:
            categoria = a["categoria"]
            lineas += ["", f"## {categoria.capitalize()}", ""]
        marca = " ⚠" if a.get("por_validar") else ""
        lineas += [
            f"### {n}. {a['es']['titulo']}{marca}",
            "",
            f"**ES:** {a['es']['contenido']}",
            "",
            f"**EN — {a['en']['titulo']}** {a['en']['contenido']}",
            "",
        ]
        if a.get("por_validar"):
            lineas += [f"> ⚠ Por confirmar: {a['por_validar']}", ""]
    return "\n".join(lineas).rstrip() + "\n"


def aviso_markdown() -> str:
    """Arma el borrador del aviso de privacidad (Ley 29733) en espanol e ingles. Sin input."""
    aviso = _leer("aviso_privacidad.json")
    lineas = [
        "# Borrador del aviso de privacidad del chat (Ley 29733)",
        "",
        f"**Versión:** `{aviso['version']}` · **Estado:** borrador para validar por el gerente y asesoría legal.",
        "",
        "El widget muestra este aviso **antes** del primer mensaje y solo abre la conversación si la persona "
        "pulsa el botón de aceptar (consentimiento previo, informado y expreso). El servidor rechaza cualquier "
        "conversación que no traiga la aceptación de la versión vigente: si el texto cambia, se cambia la "
        "versión y todos vuelven a aceptarlo.",
        "",
        "Se genera desde `app/conocimiento/aviso_privacidad.json`. Los textos entre corchetes los tiene que "
        "completar la empresa.",
        "",
        "## Pendientes antes de producción",
        "",
        "- RUC de SAVA S.A.C.",
        "- Correo para ejercer los derechos ARCO (acceso, rectificación, cancelación y oposición).",
        "- Inscripción del banco de datos «Atención al cliente» ante la Autoridad Nacional de Protección de Datos "
        "Personales.",
        "- Política de privacidad publicada en el sitio, para enlazarla desde el aviso (hoy no existe; ver "
        "`hallazgos_nucleo.md`, punto 4).",
        "- Confirmar con asesoría legal la redacción del flujo transfronterizo (proveedores de IA fuera del Perú).",
        "",
    ]
    for idioma, nombre in (("es", "Español"), ("en", "English")):
        texto = aviso[idioma]
        lineas += [f"## {nombre}", "", f"**{texto['titulo']}**", "", texto["resumen"], ""]
        lineas += [f"- {p.replace('{dias}', str(DIAS_RETENCION))}" for p in texto["puntos"]]
        lineas += ["", f"Botón: **{texto['aceptar']}**", ""]
    return "\n".join(lineas).rstrip() + "\n"


def main() -> None:
    """Escribe los dos borradores en docs/. Sin input."""
    DOCS.mkdir(exist_ok=True)
    (DOCS / "faq_borrador.md").write_text(faq_markdown(), encoding="utf-8")
    (DOCS / "aviso_privacidad_borrador.md").write_text(aviso_markdown(), encoding="utf-8")
    print("Borradores generados en", DOCS)


if __name__ == "__main__":
    main()
