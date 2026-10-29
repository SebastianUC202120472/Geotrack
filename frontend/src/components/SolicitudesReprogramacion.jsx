// Solicitudes de reprogramación que el cliente hizo desde el portal (C43-01), ligadas al pedido.
import { useEffect, useState } from "react";
import { CalendarClock, Check, X } from "lucide-react";
import Badge from "./ui/Badge";
import Button from "./ui/Button";
import { listarReprogramaciones, atenderReprogramacion } from "../services/api";

// Fecha legible corta (es-PE). Entrada: fecha ISO. Salida: "dd/mm/aa hh:mm" o "—".
const fmt = (f) => (f ? new Date(f).toLocaleString("es-PE", { dateStyle: "short", timeStyle: "short" }) : "—");

const TONO = { PENDIENTE: "warning", ACEPTADA: "success", RECHAZADA: "neutral" };
const ETIQUETA = { PENDIENTE: "Pendiente", ACEPTADA: "Aceptada", RECHAZADA: "Rechazada" };

// Qué pasa al aceptar según dónde está el pedido. Recibe el estado del pedido.
function efectoDeAceptar(estado) {
  if (estado === "FALLIDO") return "Al aceptar, el pedido se reprograma y vuelve a su zona.";
  if (estado === "ASIGNADO" || estado === "EN_RUTA") return "Al aceptar, el pedido sale de su ruta y vuelve a su zona para despacharlo en esa franja.";
  return "Al aceptar, queda anotada para despacharlo en esa franja.";
}

// Lista las solicitudes del pedido y, si permitirAtender, deja aceptar o rechazar la pendiente.
// Recibe pedidoId, pedidoEstado, permitirAtender y onAtendida (se llama con la respuesta del servidor).
export default function SolicitudesReprogramacion({ pedidoId, pedidoEstado, permitirAtender = false, onAtendida }) {
  const [solicitudes, setSolicitudes] = useState([]);
  const [nota, setNota] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let activo = true;
    listarReprogramaciones(pedidoId)
      .then((lista) => activo && setSolicitudes(lista || []))
      .catch(() => {});
    return () => { activo = false; };
  }, [pedidoId]);

  if (!solicitudes.length) return null;
  const pendiente = solicitudes.find((s) => s.estado === "PENDIENTE");

  // Acepta o rechaza la solicitud pendiente. Recibe aceptar (boolean).
  const atender = (aceptar) => {
    setEnviando(true);
    setError("");
    atenderReprogramacion(pendiente.id, { aceptar, nota: nota.trim() || undefined })
      .then((r) => onAtendida && onAtendida(r))
      .catch((e) => { setError(e.message); setEnviando(false); });
  };

  return (
    <div className="space-y-3 rounded-xl border border-info/30 bg-info-soft/60 p-4">
      <p className="flex items-center gap-1.5 text-sm font-semibold text-info-strong">
        <CalendarClock size={16} /> Reprogramación pedida por el cliente
      </p>
      <ul className="space-y-2">
        {solicitudes.map((s) => (
          <li key={s.id} className="flex items-start justify-between gap-3 text-sm">
            <div className="min-w-0">
              <p className="font-medium text-slate-800">{s.franja}</p>
              <p className="text-xs text-slate-500 nums">
                Pedida {fmt(s.creado_en)}{s.atendida_en ? ` · atendida ${fmt(s.atendida_en)}` : ""}
              </p>
              {s.respuesta && <p className="mt-0.5 text-xs text-slate-600">{s.respuesta}</p>}
            </div>
            <Badge tono={TONO[s.estado] || "neutral"} className="shrink-0">{ETIQUETA[s.estado] || s.estado}</Badge>
          </li>
        ))}
      </ul>

      {pendiente && permitirAtender && (
        <div className="space-y-2 border-t border-info/20 pt-3">
          <p className="text-xs text-slate-600">{efectoDeAceptar(pedidoEstado)}</p>
          <input
            value={nota}
            onChange={(e) => setNota(e.target.value)}
            maxLength={255}
            placeholder="Nota interna (opcional)"
            className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 placeholder:text-slate-400 outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/30"
          />
          {error && <p className="text-xs text-danger-strong">{error}</p>}
          <div className="flex gap-2">
            <Button size="sm" icon={Check} onClick={() => atender(true)} disabled={enviando}>
              {enviando ? "Guardando…" : "Aceptar"}
            </Button>
            <Button size="sm" variant="secondary" icon={X} onClick={() => atender(false)} disabled={enviando}>
              Rechazar
            </Button>
          </div>
        </div>
      )}
      {pendiente && !permitirAtender && pedidoEstado === "FALLIDO" && (
        <p className="text-xs text-slate-600">Si reprogramas el pedido, esta solicitud queda aceptada; si lo cancelas, rechazada.</p>
      )}
    </div>
  );
}
