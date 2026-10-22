import { useNavigate } from "react-router-dom";
import { ArrowUpRight } from "lucide-react";
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

// Tabla corta con los datos reales de la consulta. Recibe el bloque.
function Tabla({ bloque }) {
  return (
    <div className="overflow-hidden rounded-lg border border-slate-200">
      <p className="border-b border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-semibold text-slate-700">
        {bloque.titulo}
      </p>
      <div className="max-h-64 overflow-auto">
        <table className="w-full text-left text-xs">
          <thead className="sticky top-0 bg-white">
            <tr>
              {bloque.columnas.map((c) => (
                <th key={c} className="whitespace-nowrap px-2 py-1.5 font-semibold text-slate-500">
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {bloque.filas.map((fila, i) => (
              <tr key={i} className="border-t border-slate-100">
                {fila.map((celda, j) => (
                  <td key={j} className="whitespace-nowrap px-2 py-1.5 text-slate-700">
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

// Grafico simple de barras o torta. Recibe el bloque.
function Grafico({ bloque }) {
  const datos = bloque.datos || [];
  if (!datos.length) return null;
  return (
    <div className="rounded-lg border border-slate-200 p-2">
      <p className="px-1 pb-1 text-xs font-semibold text-slate-700">{bloque.titulo}</p>
      <div className="h-48 w-full">
        <ResponsiveContainer width="100%" height="100%">
          {bloque.forma === "torta" ? (
            <PieChart>
              <Pie data={datos} dataKey="valor" nameKey="etiqueta" outerRadius={70} label={({ etiqueta }) => etiqueta}>
                {datos.map((_, i) => (
                  <Cell key={i} fill={COLORES[i % COLORES.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          ) : (
            <BarChart data={datos} layout="vertical" margin={{ left: 8, right: 16 }}>
              <XAxis type="number" allowDecimals={false} tick={{ fontSize: 10 }} />
              <YAxis type="category" dataKey="etiqueta" width={110} tick={{ fontSize: 10 }} />
              <Tooltip />
              <Bar dataKey="valor" fill="#2563eb" radius={[0, 4, 4, 0]} />
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  );
}

// Boton que abre una pantalla del panel con los filtros aplicados. Recibe el bloque y onNavegar.
function Enlace({ bloque, onNavegar }) {
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
      className="inline-flex items-center gap-1 rounded-full border border-brand-200 bg-brand-50 px-3 py-1 text-xs font-semibold text-brand-700 transition-colors hover:bg-brand-100"
    >
      {bloque.texto}
      <ArrowUpRight size={13} />
    </button>
  );
}

// Pinta los bloques de una respuesta: primero tablas y graficos, luego los enlaces. Recibe bloques y onNavegar.
export default function BloquesRespuesta({ bloques, onNavegar }) {
  if (!bloques?.length) return null;
  const visuales = bloques.filter((b) => b.tipo === "tabla" || b.tipo === "grafico");
  const enlaces = bloques.filter((b) => b.tipo === "enlace");
  return (
    <div className="mt-2 space-y-2">
      {visuales.map((b, i) =>
        b.tipo === "tabla" ? <Tabla key={i} bloque={b} /> : <Grafico key={i} bloque={b} />
      )}
      {enlaces.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {enlaces.map((b) => (
            <Enlace key={b.ruta} bloque={b} onNavegar={onNavegar} />
          ))}
        </div>
      )}
    </div>
  );
}
