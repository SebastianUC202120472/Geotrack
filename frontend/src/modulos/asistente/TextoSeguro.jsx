// Muestra la respuesta del asistente como TEXTO saneado. Solo entiende **negritas**,
// *cursivas* y listas con "- " o "1. ". Todo se pinta como nodos de texto de React: aunque
// la IA devolviera HTML o un <script>, se veria escrito y nunca se ejecutaria (anti-XSS).
// Las tablas Markdown se omiten: el detalle va en la tabla que arma el servidor (el servidor
// ya las quita; esto cubre respuestas guardadas antes de ese cambio).

// Negrita (**x**) o cursiva (*x*, sin espacio junto a los asteriscos: "2 * 3 * 4" no es cursiva).
const RE_FORMATO = /(\*\*[^*\n]+\*\*|\*(?=\S)[^*\n]*?\S\*|\*\S\*)/g;
const RE_FILA_TABLA = /^\s*\|.*\|\s*$/;
const RE_SEPARADOR_TABLA = /^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?\s*$/;

// Parte una linea en texto normal, negritas y cursivas. Recibe la linea y una clave base.
function enLinea(linea, clave) {
  return linea.split(RE_FORMATO).map((parte, i) => {
    if (parte.length > 4 && parte.startsWith("**") && parte.endsWith("**")) {
      return (
        <strong key={`${clave}-${i}`} className="font-semibold text-slate-900">
          {parte.slice(2, -2)}
        </strong>
      );
    }
    if (parte.length > 2 && parte.startsWith("*") && parte.endsWith("*") && !parte.startsWith("**")) {
      return (
        <em key={`${clave}-${i}`} className="italic">
          {parte.slice(1, -1)}
        </em>
      );
    }
    return parte;
  });
}

// Dice si una linea es fila o separador de una tabla Markdown. Recibe la linea.
const esFilaTabla = (linea) => (RE_FILA_TABLA.test(linea) && linea.split("|").length > 2) || RE_SEPARADOR_TABLA.test(linea);

// Agrupa las lineas en parrafos y listas. Recibe el texto completo.
function agrupar(texto) {
  const grupos = [];
  for (const linea of texto.split("\n")) {
    if (esFilaTabla(linea)) continue;
    const item = linea.match(/^\s*(?:[-*•]|\d+[.)])\s+(.*)$/);
    const ultimo = grupos[grupos.length - 1];
    if (item) {
      if (ultimo?.tipo === "lista") ultimo.items.push(item[1]);
      else grupos.push({ tipo: "lista", items: [item[1]] });
    } else if (linea.trim() === "") {
      grupos.push({ tipo: "vacio" });
    } else if (ultimo?.tipo === "parrafo") {
      ultimo.lineas.push(linea);
    } else {
      grupos.push({ tipo: "parrafo", lineas: [linea] });
    }
  }
  return grupos.filter((g) => g.tipo !== "vacio");
}

// Texto del asistente con formato minimo y seguro. Recibe texto (string).
export default function TextoSeguro({ texto }) {
  return (
    <div className="space-y-2 break-words">
      {agrupar(texto || "").map((grupo, i) =>
        grupo.tipo === "lista" ? (
          <ul key={i} className="list-disc space-y-0.5 pl-5">
            {grupo.items.map((item, j) => (
              <li key={j}>{enLinea(item, `${i}-${j}`)}</li>
            ))}
          </ul>
        ) : (
          <p key={i}>
            {grupo.lineas.map((linea, j) => (
              <span key={j}>
                {j > 0 && <br />}
                {enLinea(linea, `${i}-${j}`)}
              </span>
            ))}
          </p>
        )
      )}
    </div>
  );
}
