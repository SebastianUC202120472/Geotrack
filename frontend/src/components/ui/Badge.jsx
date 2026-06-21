// Etiqueta de estado con colores semánticos consistentes en todo el panel.
// <Badge tono="success">…</Badge> para uso libre, o <EstadoBadge estado="EN_RUTA" />
// que ya conoce el color de cada estado de pedido / ruta / vehículo.

const tonos = {
  neutral: "bg-slate-100 text-slate-600",
  info: "bg-info-soft text-info-strong",
  brand: "bg-brand-50 text-brand-700",
  success: "bg-success-soft text-success-strong",
  warning: "bg-warning-soft text-warning-strong",
  danger: "bg-danger-soft text-danger-strong",
};

export default function Badge({ tono = "neutral", className = "", children }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ${tonos[tono]} ${className}`}
    >
      {children}
    </span>
  );
}

// Estado -> tono. Lo que no esté mapeado cae en "neutral".
const mapaEstados = {
  PENDIENTE: "warning",
  ASIGNADO: "info",
  EN_RUTA: "info",
  EN_PROGRESO: "info",
  CREADA: "neutral",
  ENTREGADO: "success",
  FINALIZADA: "success",
  DISPONIBLE: "success",
  FALLIDO: "danger",
  GEOCODIFICACION_FALLIDA: "danger",
};

// Color del punto por tono (coincide con los semánticos).
const puntoPorTono = {
  neutral: "bg-slate-400",
  info: "bg-info",
  brand: "bg-brand-600",
  success: "bg-success",
  warning: "bg-warning",
  danger: "bg-danger",
};

export function EstadoBadge({ estado }) {
  if (!estado) return <Badge>—</Badge>;
  const tono = mapaEstados[estado] || "neutral";
  // Mostramos el texto en minúscula con la inicial en mayúscula, más legible.
  const texto = estado.replaceAll("_", " ").toLowerCase();
  return (
    <Badge tono={tono} className="capitalize">
      <span className={`h-1.5 w-1.5 rounded-full ${puntoPorTono[tono]}`} />
      {texto}
    </Badge>
  );
}
