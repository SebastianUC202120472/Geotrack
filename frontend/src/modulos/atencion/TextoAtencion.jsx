// Muestra la respuesta del asistente como TEXTO seguro (anti-XSS): todo se pinta como nodos de
// texto de React. Solo entiende **negritas**, listas con "- " o "1. " y rutas del propio sitio
// ("/portal", "/#reclamos"), que se vuelven enlaces internos. Cualquier otra cosa se ve escrita.
// Es una copia reducida del renderizador del asistente del panel, para no acoplar los módulos.
const RE_PARTES = /(\*\*[^*\n]+\*\*|(?<![\w/])\/(?:portal|#reclamos|#contacto|#cobertura)\b)/g;

// Parte una línea en texto, negritas y rutas internas. Recibe la línea y una clave base.
function enLinea(linea, clave) {
  return linea.split(RE_PARTES).map((parte, i) => {
    if (parte.length > 4 && parte.startsWith("**") && parte.endsWith("**")) {
      return <strong key={`${clave}-${i}`}>{parte.slice(2, -2)}</strong>;
    }
    if (/^\/(portal|#reclamos|#contacto|#cobertura)$/.test(parte)) {
      return (
        <a key={`${clave}-${i}`} href={parte} className="atn-enlace">
          {parte === "/portal" ? "portal de clientes" : parte.slice(2)}
        </a>
      );
    }
    return parte;
  });
}

// Agrupa las líneas en párrafos y listas. Recibe el texto completo.
function agrupar(texto) {
  const grupos = [];
  for (const linea of texto.split("\n")) {
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

// Texto del asistente con formato mínimo y seguro. Recibe texto (string).
export default function TextoAtencion({ texto }) {
  return (
    <div className="atn-texto">
      {agrupar(texto || "").map((grupo, i) =>
        grupo.tipo === "lista" ? (
          <ul key={i}>
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
