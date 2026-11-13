import { useSearchParams } from "react-router-dom";

// Pestañas de una página que guardan la elegida en la URL (?vista=...), para poder enlazarla.
// Recibe vistas ([id, nombre, Icono], la primera es la de por defecto) y etiqueta (accesible).
// Devuelve [vistaActual, elementoDePestañas].
export function usePestanasPagina(vistas, etiqueta) {
  const [params, setParams] = useSearchParams();
  const porDefecto = vistas[0][0];
  const pedida = params.get("vista");
  const vista = vistas.some(([id]) => id === pedida) ? pedida : porDefecto;

  const pestanas = (
    <nav className="flex gap-1 overflow-x-auto border-b border-slate-200" aria-label={etiqueta}>
      {vistas.map(([id, nombre, Icono]) => (
        <button
          key={id}
          type="button"
          onClick={() => setParams(id === porDefecto ? {} : { vista: id }, { replace: true })}
          aria-current={vista === id ? "page" : undefined}
          className={`group -mb-px flex shrink-0 items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-semibold transition-colors ${
            vista === id ? "border-brand-600 text-brand-700" : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          <Icono size={16} className="transition-transform duration-300 group-hover:-translate-y-0.5 group-hover:scale-110" />
          {nombre}
        </button>
      ))}
    </nav>
  );
  return [vista, pestanas];
}
