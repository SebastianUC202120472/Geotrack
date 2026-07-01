import { useState } from "react";
import { Search, Package, MapPin, Loader2, AlertCircle, Clock } from "lucide-react";
import SectionCard from "./ui/SectionCard";
import EmptyState from "./ui/EmptyState";
import Button from "./ui/Button";
import { EstadoBadge } from "./ui/Badge";
import { obtenerHistorial } from "../services/api";

// Pestaña de trazabilidad: buscador por código de paquete, muestra ficha y línea de tiempo.
export default function TabTrazabilidad() {
  const [codigo, setCodigo] = useState("");
  const [historial, setHistorial] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState("");
  const [buscado, setBuscado] = useState(false);

  // Lanza la búsqueda del historial del código ingresado (PD-001, RT-001…).
  const buscar = (e) => {
    e.preventDefault();
    if (!codigo.trim()) return;
    setCargando(true);
    setError("");
    setHistorial(null);
    setBuscado(true);
    obtenerHistorial(codigo.trim())
      .then((data) => {
        setCargando(false);
        setHistorial(data);
      })
      .catch((err) => {
        setCargando(false);
        setError(err.message || "No se encontró el paquete.");
      });
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="rounded-card border border-slate-200 bg-white p-5 shadow-card animate-fade-up">
        <form onSubmit={buscar} className="flex flex-col gap-3 sm:flex-row">
          <div className="relative flex-1">
            <Search size={18} className="pointer-events-none absolute left-3.5 top-3 text-slate-400" />
            <input
              value={codigo}
              onChange={(e) => setCodigo(e.target.value)}
              placeholder="Código del paquete (ej. PD-001)"
              aria-label="Código del paquete"
              className="w-full rounded-xl border border-slate-200 bg-white py-2.5 pl-10 pr-3.5 text-sm text-slate-800 placeholder:text-slate-400 outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/30"
            />
          </div>
          <Button type="submit" icon={cargando ? undefined : Search} disabled={cargando}>
            {cargando ? <Loader2 className="animate-spin" size={18} /> : "Buscar"}
          </Button>
        </form>
      </div>

      {cargando && (
        <div className="flex items-center justify-center py-8 text-sm text-slate-500 animate-fade-up">
          <Loader2 className="animate-spin mr-2" size={18} /> Buscando paquete…
        </div>
      )}

      {error && (
        <div className="rounded-card border border-danger/30 bg-white p-5 shadow-card animate-fade-up">
          <div className="flex items-center gap-3 text-danger-strong">
            <AlertCircle size={22} /> {error}
          </div>
        </div>
      )}

      {!buscado && !cargando && (
        <div className="animate-fade-up" style={{ animationDelay: "80ms" }}>
          <EmptyState
            icon={Search}
            title="Ingresa el código de un paquete"
            description="Escribe el código (ej. PD-001) en el campo de arriba y pulsa Buscar para ver su trazabilidad completa."
          />
        </div>
      )}

      {historial && (
        <div className="grid gap-6 lg:grid-cols-3 animate-fade-up" style={{ animationDelay: "60ms" }}>
          <SectionCard title="Ficha del pedido">
            <div className="mb-4 flex items-center gap-3">
              <span className="rounded-xl bg-brand-600 p-3 text-white"><Package size={22} /></span>
              <div>
                <p className="font-semibold text-slate-900 nums">{historial.codigo}</p>
                <EstadoBadge estado={historial.estado_actual} />
              </div>
            </div>
            <div className="space-y-3">
              <Dato etiqueta="Cliente" valor={historial.cliente_origen} />
              <Dato etiqueta="Destino" valor={historial.direccion_destino} icono={MapPin} />
              <Dato etiqueta="Distrito" valor={historial.distrito || "—"} />
              <Dato etiqueta="Ruta asignada" valor={historial.ruta_asignada || "Sin asignar"} />
              {historial.motivo_fallo && <Dato etiqueta="Motivo de fallo" valor={historial.motivo_fallo} />}
              {historial.url_evidencia && (
                <a href={historial.url_evidencia} target="_blank" rel="noreferrer"
                  className="inline-block text-sm font-medium text-brand-600 hover:underline">
                  Ver evidencia (POD)
                </a>
              )}
            </div>
          </SectionCard>

          <SectionCard title="Línea de tiempo" className="lg:col-span-2">
            {historial.eventos.length === 0 ? (
              <EmptyState
                icon={Clock}
                title="Sin eventos registrados"
                description="Este paquete aún no tiene eventos en su línea de tiempo."
              />
            ) : (
              <ol className="relative ml-2 space-y-6 border-l-2 border-slate-100">
                {historial.eventos.map((ev, i) => (
                  <li key={i} className="ml-6 animate-fade-up" style={{ animationDelay: `${i * 40}ms` }}>
                    <span className="absolute -left-[9px] h-4 w-4 rounded-full border-2 border-white bg-brand-600" />
                    <p className="font-semibold text-slate-800">{ev.evento}</p>
                    <p className="text-sm text-slate-500">{ev.descripcion}</p>
                    <p className="mt-1 text-xs text-slate-400">
                      {ev.fecha ? new Date(ev.fecha).toLocaleString("es-PE") : "Sin fecha"}
                      {ev.realizado_por ? ` · ${ev.realizado_por}` : ""}
                    </p>
                  </li>
                ))}
              </ol>
            )}
          </SectionCard>
        </div>
      )}
    </div>
  );
}

// Fila de dato etiqueta/valor con ícono opcional.
function Dato({ etiqueta, valor, icono: Icono }) {
  return (
    <div className="flex items-start gap-2 text-sm">
      {Icono && <Icono size={16} className="mt-0.5 text-slate-400" />}
      <div>
        <p className="text-slate-400">{etiqueta}</p>
        <p className="font-medium text-slate-700">{valor}</p>
      </div>
    </div>
  );
}
