// Etiqueta de estado con color semántico. Recibe tono o usa EstadoBadge para mapear estados conocidos.
import { ETIQUETAS_ESTADO } from "../../utils/estados";

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

const mapaEstados = {
  SOLICITADO: "warning",
  RECOGIDO: "success",
  INGRESADO: "success",
  POR_RECOGER: "neutral",
  OBSERVADO: "danger",
  LISTO_PARA_ENVIO: "warning",
  ASIGNADO: "info",
  EN_RUTA: "info",
  EN_PROGRESO: "info",
  CREADA: "neutral",
  ENTREGADO: "success",
  FINALIZADA: "success",
  DISPONIBLE: "success",
  FALLIDO: "danger",
  GEOCODIFICACION_FALLIDA: "danger",
  CANCELADO: "neutral",
};

const puntoPorTono = {
  neutral: "bg-slate-400",
  info: "bg-info",
  brand: "bg-brand-600",
  success: "bg-success",
  warning: "bg-warning",
  danger: "bg-danger",
};

// Muestra un Badge coloreado segun el estado del pedido/ruta. Recibe estado (string).
export function EstadoBadge({ estado }) {
  if (!estado) return <Badge>—</Badge>;
  const tono = mapaEstados[estado] || "neutral";
  const personalizado = ETIQUETAS_ESTADO[estado];
  const texto = personalizado || estado.replaceAll("_", " ").toLowerCase();
  return (
    <Badge tono={tono} className={personalizado ? "" : "capitalize"}>
      <span className={`h-1.5 w-1.5 rounded-full ${puntoPorTono[tono]}`} />
      {texto}
    </Badge>
  );
}
