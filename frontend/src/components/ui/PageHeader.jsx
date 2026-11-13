// Cabecera reutilizable: título, subtítulo y acciones (children). Recibe titulo, subtitulo,
// children y seccion (true = encabezado de una sección dentro de otra página, más pequeño).
export default function PageHeader({ titulo, subtitulo, children, seccion = false }) {
  const Titulo = seccion ? "h2" : "h1";
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <Titulo className={`${seccion ? "text-lg" : "text-2xl"} font-bold tracking-tight text-slate-900`}>{titulo}</Titulo>
        {subtitulo && <p className="mt-1 text-sm text-slate-500">{subtitulo}</p>}
      </div>
      {children && <div className="flex flex-wrap items-center gap-2">{children}</div>}
    </div>
  );
}
