import { useState } from "react";
import { Search, Package, MapPin, Loader2, AlertCircle } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import Card from "../components/ui/Card";
import Input from "../components/ui/Input";
import Button from "../components/ui/Button";
import { EstadoBadge } from "../components/ui/Badge";
import { obtenerHistorial } from "../services/api";

// Trazabilidad de un paquete (CUS-35): búsqueda por código (PD-001) + ficha y
// línea de tiempo de eventos.
export default function Trazabilidad() {
  const [codigo, setCodigo] = useState("");
  const [historial, setHistorial] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState("");

  const buscar = async (e) => {
    e.preventDefault();
    if (!codigo.trim()) return;
    setCargando(true);
    setError("");
    setHistorial(null);
    try {
      setHistorial(await obtenerHistorial(codigo.trim()));
    } catch (err) {
      setError(err.message || "No se encontró el paquete.");
    } finally {
      setCargando(false);
    }
  };

  return (
    <div className="space-y-6 p-6 lg:p-8">
      <PageHeader titulo="Trazabilidad de Paquetes" subtitulo="Consulta la línea de tiempo de un pedido (CUS-35)." />

      <Card>
        <form onSubmit={buscar} className="flex flex-col gap-3 sm:flex-row">
          <input
            value={codigo}
            onChange={(e) => setCodigo(e.target.value)}
            placeholder="Código del paquete (ej. PD-001)"
            aria-label="Código del paquete"
            className="flex-1 rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-800 placeholder:text-slate-400 outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/30"
          />
          <Button type="submit" icon={cargando ? undefined : Search} disabled={cargando}>
            {cargando ? <Loader2 className="animate-spin" size={18} /> : "Buscar"}
          </Button>
        </form>
      </Card>

      {error && (
        <Card className="border-danger/30">
          <div className="flex items-center gap-3 text-danger-strong">
            <AlertCircle size={22} /> {error}
          </div>
        </Card>
      )}

      {historial && (
        <div className="grid gap-6 lg:grid-cols-3">
          <Card title="Ficha del pedido">
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
          </Card>

          <Card title="Línea de tiempo" className="lg:col-span-2">
            {historial.eventos.length === 0 ? (
              <p className="text-sm text-slate-400">Este paquete aún no tiene eventos registrados.</p>
            ) : (
              <ol className="relative ml-2 space-y-6 border-l-2 border-slate-100">
                {historial.eventos.map((ev, i) => (
                  <li key={i} className="ml-6">
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
          </Card>
        </div>
      )}
    </div>
  );
}

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
