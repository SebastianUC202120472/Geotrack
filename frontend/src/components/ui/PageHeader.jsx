// Cabecera de página: título + subtítulo a la izquierda y acciones a la derecha.
// Unifica el encabezado de todas las pantallas (antes cada página repetía su
// propio título, que además chocaba con la barra superior).
export default function PageHeader({ titulo, subtitulo, children }) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">{titulo}</h1>
        {subtitulo && <p className="mt-1 text-sm text-slate-500">{subtitulo}</p>}
      </div>
      {children && <div className="flex items-center gap-2">{children}</div>}
    </div>
  );
}
