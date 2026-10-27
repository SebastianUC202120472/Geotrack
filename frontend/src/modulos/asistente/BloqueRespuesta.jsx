import { useNavigate } from "react-router-dom";
import { ArrowUpRight, Link2 } from "lucide-react";
import {
  Bar,
  BarChart,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const COLORES = ["#2563eb", "#16a34a", "#f59e0b", "#dc2626", "#0ea5e9", "#7c3aed", "#64748b", "#db2777"];

// Titulo de una tabla o grafico; en la vista grande lleva el enlace a su fuente. Recibe titulo, fuente y onNavegar.
function Titulo({ titulo, fuente, onNavegar, className = "" }) {
  return (
    <div className={`flex items-center justify-between gap-2 ${className}`}>
      <p className="text-xs font-semibold text-slate-700">{titulo}</p>
      {fuente && <Enlace bloque={fuente} onNavegar={onNavegar} discreto />}
    </div>
  );
}

// Columnas cuyo texto pasa a otra linea en vez de estirar la tabla (Motivo de fallo, Detalle...):
// las que tienen alguna celda de mas de LARGO_CELDA caracteres. Recibe el bloque.
const LARGO_CELDA = 28;
function columnasLargas(bloque) {
  return bloque.columnas.map((_, j) => bloque.filas.some((fila) => String(fila[j] ?? "").length > LARGO_CELDA));
}

// Tabla corta con los datos reales de la consulta. Recibe el bloque, si es grande y la fuente.
function Tabla({ bloque, grande, fuente, onNavegar }) {
  const largas = columnasLargas(bloque);
  // Texto largo: varias lineas, con un ancho minimo para que no quede una palabra por linea.
  const ajuste = (j) =>
    largas[j] ? `whitespace-normal break-words ${grande ? "min-w-[14rem] max-w-md" : "min-w-[11rem] max-w-[16rem]"}` : "whitespace-nowrap";
  return (
    <div className="overflow-hidden rounded-lg border border-slate-200">
      <Titulo
        titulo={bloque.titulo}
        fuente={fuente}
        onNavegar={onNavegar}
        className="border-b border-slate-200 bg-slate-50 px-3 py-1.5"
      />
      <div className={`${grande ? "max-h-[28rem]" : "max-h-64"} overflow-auto`}>
        <table className={`w-full text-left ${grande ? "text-sm" : "text-xs"}`}>
          <thead className="sticky top-0 bg-white">
            <tr>
              {bloque.columnas.map((c, j) => (
                <th key={c} className={`${ajuste(j)} px-2 py-1.5 align-bottom font-semibold text-slate-500`}>
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {bloque.filas.map((fila, i) => (
              <tr key={i} className="border-t border-slate-100">
                {fila.map((celda, j) => (
                  <td key={j} className={`${ajuste(j)} px-2 py-1.5 align-top text-slate-700`}>
                    {String(celda)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {bloque.total > bloque.filas.length && (
        <p className="border-t border-slate-100 px-3 py-1 text-[11px] text-slate-500">
          Mostrando {bloque.filas.length} de {bloque.total}
        </p>
      )}
    </div>
  );
}

// Grafico simple de barras o torta. Recibe el bloque, si es grande y la fuente.
function Grafico({ bloque, grande, fuente, onNavegar }) {
  const datos = bloque.datos || [];
  if (!datos.length) return null;
  const letra = grande ? 12 : 10;
  // En la vista grande las barras crecen con la cantidad de categorias.
  const alto = grande ? Math.max(320, datos.length * 34) : 192;
  return (
    <div className="rounded-lg border border-slate-200 p-2">
      <Titulo titulo={bloque.titulo} fuente={fuente} onNavegar={onNavegar} className="px-1 pb-1" />
      <div className="w-full" style={{ height: bloque.forma === "torta" ? (grande ? 360 : 192) : alto }}>
        <ResponsiveContainer width="100%" height="100%">
          {bloque.forma === "torta" ? (
            <PieChart>
              <Pie
                data={datos}
                dataKey="valor"
                nameKey="etiqueta"
                outerRadius={grande ? 130 : 70}
                label={({ etiqueta, valor }) => (grande ? `${etiqueta}: ${valor}` : etiqueta)}
              >
                {datos.map((_, i) => (
                  <Cell key={i} fill={COLORES[i % COLORES.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          ) : (
            <BarChart data={datos} layout="vertical" margin={{ left: 8, right: grande ? 32 : 16 }}>
              <XAxis type="number" allowDecimals={false} tick={{ fontSize: letra }} />
              <YAxis type="category" dataKey="etiqueta" width={grande ? 180 : 110} tick={{ fontSize: letra }} />
              <Tooltip />
              <Bar dataKey="valor" fill="#2563eb" radius={[0, 4, 4, 0]} />
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  );
}

// Boton que abre una pantalla del panel con los filtros aplicados. Recibe el bloque, onNavegar y discreto.
function Enlace({ bloque, onNavegar, discreto = false }) {
  const navigate = useNavigate();
  // Solo rutas internas del panel: nunca se abre un enlace externo.
  if (typeof bloque.ruta !== "string" || !bloque.ruta.startsWith("/panel")) return null;
  return (
    <button
      type="button"
      onClick={() => {
        navigate(bloque.ruta);
        onNavegar?.();
      }}
      title={discreto ? `Fuente: ${bloque.texto}` : undefined}
      className={
        discreto
          ? "inline-flex shrink-0 items-center gap-1 text-[11px] font-semibold text-brand-600 hover:text-brand-700 hover:underline"
          : "inline-flex items-center gap-1 rounded-full border border-brand-200 bg-brand-50 px-3 py-1 text-xs font-semibold text-brand-700 transition-colors hover:bg-brand-100"
      }
    >
      {discreto ? "Ver fuente" : bloque.texto}
      <ArrowUpRight size={13} />
    </button>
  );
}

// Pinta los bloques de una respuesta: primero tablas y graficos, luego los enlaces.
// En la vista grande (grande=true) cada tabla o grafico muestra "Ver fuente" cuando la
// respuesta tiene una sola pantalla de origen, y los enlaces van bajo "Fuente de los datos".
// Recibe bloques, onNavegar y grande.
export default function BloquesRespuesta({ bloques, onNavegar, grande = false }) {
  if (!bloques?.length) return null;
  const visuales = bloques.filter((b) => b.tipo === "tabla" || b.tipo === "grafico");
  const enlaces = bloques.filter((b) => b.tipo === "enlace");
  const fuente = grande && enlaces.length === 1 ? enlaces[0] : null;
  return (
    <div className={`mt-2 ${grande ? "space-y-3" : "space-y-2"}`}>
      {visuales.map((b, i) =>
        b.tipo === "tabla" ? (
          <Tabla key={i} bloque={b} grande={grande} fuente={fuente} onNavegar={onNavegar} />
        ) : (
          <Grafico key={i} bloque={b} grande={grande} fuente={fuente} onNavegar={onNavegar} />
        )
      )}
      {enlaces.length > 0 && (
        <div className="flex flex-wrap items-center gap-1.5">
          {grande && (
            <span className="mr-1 inline-flex items-center gap-1 text-[11px] font-semibold uppercase tracking-wide text-slate-400">
              <Link2 size={12} /> Fuente de los datos
            </span>
          )}
          {enlaces.map((b) => (
            <Enlace key={b.ruta} bloque={b} onNavegar={onNavegar} />
          ))}
        </div>
      )}
    </div>
  );
}
