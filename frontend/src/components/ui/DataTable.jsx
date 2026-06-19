import Skeleton from "./Skeleton";
import EmptyState from "./EmptyState";

// Tabla reutilizable con cabecera sticky, hover de fila y estados de carga/vacío.
// Entrada:
//   columns: [{ key, header, render?(fila), className? }]
//   rows: array de objetos
//   rowKey: (fila) => string|number  (clave única)
//   loading (bool): muestra filas skeleton
//   empty: { icon?, title, description? }  (cuando no hay filas)
//   onRowClick?: (fila) => void
export default function DataTable({ columns, rows, rowKey, loading = false, empty, onRowClick }) {
  return (
    <div className="overflow-hidden rounded-card border border-slate-200 bg-white shadow-card">
      <table className="w-full border-collapse text-sm">
        <thead className="sticky top-0 z-10 bg-warm-50">
          <tr>
            {columns.map((c) => (
              <th
                key={c.key}
                className={`px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-slate-400 ${c.className || ""}`}
              >
                {c.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {loading
            ? Array.from({ length: 6 }).map((_, i) => (
                <tr key={`sk-${i}`} className="border-t border-warm-100">
                  {columns.map((c) => (
                    <td key={c.key} className="px-4 py-3">
                      <Skeleton className="h-4 w-3/4" />
                    </td>
                  ))}
                </tr>
              ))
            : rows.map((fila) => (
                <tr
                  key={rowKey(fila)}
                  onClick={onRowClick ? () => onRowClick(fila) : undefined}
                  className={`border-t border-warm-100 transition-colors hover:bg-warm-50 ${onRowClick ? "cursor-pointer" : ""}`}
                >
                  {columns.map((c) => (
                    <td key={c.key} className={`px-4 py-3 text-slate-700 ${c.className || ""}`}>
                      {c.render ? c.render(fila) : fila[c.key]}
                    </td>
                  ))}
                </tr>
              ))}
        </tbody>
      </table>
      {!loading && rows.length === 0 && empty && (
        <EmptyState icon={empty.icon} title={empty.title} description={empty.description} />
      )}
    </div>
  );
}
