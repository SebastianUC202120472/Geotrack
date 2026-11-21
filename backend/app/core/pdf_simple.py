# Generador minimo de PDF en texto plano, sin librerias externas.
# Sirve para la ficha de mantenimiento: titulo, subtitulo y lineas de detalle.
# Usa Helvetica con WinAnsiEncoding, que cubre los acentos del espanol.
import zlib

_ANCHO = 595  # A4 en puntos
_ALTO = 842
_MARGEN = 54
_ALTURA_LINEA = 16
_MAX_PRIMERA = 56
_MAX_OTRAS = 64
_ANCHO_TEXTO = 95


def _escapar(texto: str) -> str:
    """Escapa los caracteres reservados de una cadena PDF. Recibe el texto."""

    return texto.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _linea(texto: str, y: float, negrita: bool = False, tamano: int = 10) -> str:
    """Arma una instruccion PDF para dibujar una linea. Recibe el texto y Y."""

    seguro = texto.encode("latin-1", errors="replace").decode("latin-1")[:_ANCHO_TEXTO]
    fuente = "F2" if negrita else "F1"
    return (
        f"BT /{fuente} {tamano} Tf 1 0 0 1 {_MARGEN} {y} Tm "
        f"({_escapar(seguro)}) Tj ET"
    )


def _pagina(
    titulo: str,
    subtitulo: str | None,
    lineas: list,
    numero: int,
    total: int,
) -> bytes:
    """Dibuja una pagina con encabezado, lineas y pie. Recibe las lineas."""

    comandos = []
    y = float(_ALTO - _MARGEN)
    if numero == 1:
        comandos.append(_linea(titulo, y, negrita=True, tamano=18))
        y -= 26
        if subtitulo:
            comandos.append(_linea(subtitulo, y, tamano=11))
            y -= 26
    else:
        comandos.append(_linea(f"{titulo} (continuacion)", y, negrita=True, tamano=13))
        y -= 30

    for texto in lineas:
        if y < _MARGEN + 22:
            break
        comandos.append(_linea(str(texto), y))
        y -= _ALTURA_LINEA

    comandos.append(
        f"BT /F1 8 Tf 1 0 0 1 {_MARGEN} 28 Tm "
        f"(Pagina {numero} de {total} - SAVA S.A.C.) Tj ET"
    )
    return "\n".join(comandos).encode("latin-1", errors="replace")


def construir_pdf(titulo: str, lineas: list, subtitulo: str | None = None) -> bytes:
    """Devuelve un PDF de una o varias paginas. Recibe titulo y lineas de texto."""

    textos = [str(fila) for fila in lineas]
    paginas: list = []
    inicio = 0
    while inicio < len(textos):
    # La primera pagina tiene menos espacio por el encabezado.
        limite = _MAX_PRIMERA if not paginas else _MAX_OTRAS
        paginas.append(textos[inicio : inicio + limite])
        inicio += limite
    if not paginas:
        paginas = [[]]

    total = len(paginas)
    streams = [
        zlib.compress(
            _pagina(titulo, subtitulo, grupo, indice + 1, total),
        )
        for indice, grupo in enumerate(paginas)
    ]

    numero_fuente_normal = 3 + total
    numero_fuente_titulo = 4 + total
    numero_contenido = 5 + total
    hijos = " ".join(f"{3 + indice} 0 R" for indice in range(total))

    objetos = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        f"<< /Type /Pages /Kids [{hijos}] /Count {total} >>".encode(),
    ]
    for indice in range(total):
        objetos.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {_ANCHO} {_ALTO}] "
            f"/Resources << /Font << /F1 {numero_fuente_normal} 0 R "
            f"/F2 {numero_fuente_titulo} 0 R >> >> "
            f"/Contents {numero_contenido + indice} 0 R >>".encode()
        )
    objetos.extend(
        [
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>",
        ]
    )
    for stream in streams:
        objetos.append(
            f"<< /Length {len(stream)} /Filter /FlateDecode >>\nstream\n".encode()
            + stream
            + b"\nendstream"
        )

    salida = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    desplazamientos = []
    for numero, objeto in enumerate(objetos, start=1):
        desplazamientos.append(len(salida))
        salida.extend(f"{numero} 0 obj\n".encode())
        salida.extend(objeto)
        salida.extend(b"\nendobj\n")

    inicio_xref = len(salida)
    salida.extend(f"xref\n0 {len(objetos) + 1}\n".encode())
    salida.extend(b"0000000000 65535 f \n")
    for desplazamiento in desplazamientos:
        salida.extend(f"{desplazamiento:010d} 00000 n \n".encode())
    salida.extend(
        f"trailer\n<< /Size {len(objetos) + 1} /Root 1 0 R >>\n"
        f"startxref\n{inicio_xref}\n%%EOF\n".encode()
    )
    return bytes(salida)
