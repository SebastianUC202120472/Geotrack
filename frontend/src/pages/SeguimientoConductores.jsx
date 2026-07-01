import { useEffect, useState } from "react";
import { RefreshCw, MapPin, Users, Wifi, WifiOff, Wrench } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import KpiCard from "../components/ui/KpiCard";
import SectionCard from "../components/ui/SectionCard";
import EmptyState from "../components/ui/EmptyState";
import LiveBadge from "../components/ui/LiveBadge";
import Button from "../components/ui/Button";
import MapaFlota from "../components/MapaFlota";
import { obtenerUbicacionesFlota } from "../services/api";
import { haceCuanto } from "../utils/formatoFecha";

const REFRESCO_MS = 15000; // intervalo de polling en ms

// Colores por conductor; se comparten con sus marcadores en el mapa.
const COLORES = ["#2563EB", "#DC2626", "#059669", "#D97706", "#7C3AED", "#DB2777", "#0891B2", "#65A30D"];

// Muestra posición en vivo de conductores con ruta activa y sus paradas.
export default function SeguimientoConductores() {
  const [ubicaciones, setUbicaciones] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [seleccionado, setSeleccionado] = useState(null); // conductor_id seleccionado; null = todos
  const [filtroCapa, setFiltroCapa] = useState("TODO");   // TODO | CONDUCTORES | PEDIDOS

  // Recarga manualmente los datos del mapa.
  const actualizar = () => {
    setCargando(true);
    obtenerUbicacionesFlota()
      .then(setUbicaciones)
      .catch((err) => console.error("No se pudo cargar el mapa:", err.message))
      .finally(() => setCargando(false));
  };

  // Carga inicial y polling cada 15 s; setState solo en callbacks para evitar warnings.
  useEffect(() => {
    let activo = true;
    const traer = () =>
      obtenerUbicacionesFlota()
        .then((u) => activo && setUbicaciones(u))
        .catch(() => {})
        .finally(() => activo && setCargando(false));
    traer();
    const id = setInterval(traer, REFRESCO_MS);
    return () => {
      activo = false;
      clearInterval(id);
    };
  }, []);

  // Métricas derivadas de los datos cargados.
  const totalConductores = ubicaciones.length;
  const enLinea = ubicaciones.filter((c) => c.en_linea).length;
  const sinSenal = totalConductores - enLinea;
  const pendientesDe = (c) => c.paradas?.filter((p) => (p.estado || "PENDIENTE") === "PENDIENTE").length ?? 0;
  const totalParadas = ubicaciones.reduce((acc, c) => acc + pendientesDe(c), 0);
  const pausados = ubicaciones.filter((u) => u.pausado).length;

  const conductores = ubicaciones.map((c, i) => ({ ...c, _color: COLORES[i % COLORES.length] }));
  // Si hay seleccionado, el mapa muestra solo ese conductor.
  const conductoresVisibles = seleccionado != null ? conductores.filter((c) => c.conductor_id === seleccionado) : conductores;

  return (
    <div className="space-y-6 p-6 lg:p-8">
      <div className="animate-fade-up">
        <PageHeader
          titulo="Seguimiento de Conductores"
          subtitulo="Ubicación en vivo de cada conductor con ruta activa y sus pedidos pendientes."
        >
          {/* Selector de capa del mapa */}
          <div className="flex rounded-lg border border-slate-200 bg-white p-0.5 text-xs font-semibold" role="group" aria-label="Filtrar mapa">
            {[["TODO", "Todo"], ["CONDUCTORES", "Conductores"], ["PEDIDOS", "Pedidos"]].map(([valor, etiqueta]) => (
              <button
                key={valor}
                type="button"
                onClick={() => setFiltroCapa(valor)}
                className={`rounded-md px-2.5 py-1.5 transition-colors ${
                  filtroCapa === valor ? "bg-brand-600 text-white" : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                {etiqueta}
              </button>
            ))}
          </div>
          <LiveBadge tone="success">En vivo</LiveBadge>
          <Button variant="secondary" icon={RefreshCw} onClick={actualizar}>
            Actualizar
          </Button>
        </PageHeader>
      </div>

      {!cargando && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-5 animate-fade-up">
          <KpiCard
            label="Conductores activos"
            value={totalConductores}
            icon={Users}
            tone="brand"
            live={totalConductores > 0}
          />
          <KpiCard
            label="En línea"
            value={enLinea}
            icon={Wifi}
            tone="success"
            live={enLinea > 0}
          />
          <KpiCard
            label="Sin señal"
            value={sinSenal}
            icon={WifiOff}
            tone={sinSenal > 0 ? "warning" : "info"}
          />
          <KpiCard
            label="Paradas en ruta"
            value={totalParadas}
            icon={MapPin}
            tone="info"
          />
          <KpiCard
            label="Pausados"
            value={pausados}
            icon={Wrench}
            tone={pausados > 0 ? "danger" : "info"}
          />
        </div>
      )}

      {cargando ? (
        <div className="animate-fade-up rounded-xl border border-slate-200 bg-white shadow-card p-10 text-center text-sm text-slate-500">
          Cargando mapa…
        </div>
      ) : ubicaciones.length === 0 ? (
        <div className="animate-fade-up">
          <SectionCard>
            <EmptyState
              icon={MapPin}
              title="Sin conductores en ruta"
              description="No hay conductores con ruta activa enviando su ubicación ahora mismo."
              action={
                <Button variant="secondary" icon={RefreshCw} onClick={actualizar}>
                  Volver a intentar
                </Button>
              }
            />
          </SectionCard>
        </div>
      ) : (
        <div className="flex flex-col gap-4 lg:flex-row animate-fade-up">
          <div className="w-full lg:w-72 shrink-0">
            <SectionCard
              title="Conductores"
              subtitle={`${totalConductores} en ruta`}
              className="h-full"
              action={
                seleccionado != null ? (
                  <button
                    type="button"
                    onClick={() => setSeleccionado(null)}
                    className="text-xs font-semibold text-brand-600 hover:text-brand-700"
                  >
                    Ver todos
                  </button>
                ) : null
              }
            >
              <ul className="space-y-1 -mx-5 px-0">
                {conductores.map((c) => {
                  const activo = seleccionado === c.conductor_id;
                  return (
                    <li key={c.conductor_id}>
                      <button
                        type="button"
                        onClick={() => setSeleccionado(seleccionado === c.conductor_id ? null : c.conductor_id)}
                        className={`flex w-full items-start gap-3 rounded-lg px-5 py-3 text-left transition-colors ${
                          activo ? "bg-brand-50" : "hover:bg-slate-50"
                        }`}
                      >
                        <span
                          className={`mt-1 h-3 w-3 shrink-0 rounded-full border border-white shadow ${c.en_linea ? "live-dot" : ""}`}
                          style={{ backgroundColor: c._color, opacity: c.en_linea ? 1 : 0.5 }}
                          aria-hidden="true"
                        />
                        <div className="min-w-0">
                          <p className="truncate text-sm font-semibold text-slate-900">
                            {c.conductor || "Conductor"}
                          </p>
                          {c.pausado && (
                            <span className="inline-block rounded-full bg-danger-soft px-2 py-0.5 text-[11px] font-semibold text-danger-strong">🛠️ Pausado</span>
                          )}
                          <p className="truncate text-xs text-slate-500">{c.ruta || "Sin ruta"}</p>
                          <p className="mt-0.5 text-xs text-slate-400">
                            {pendientesDe(c)} parada{pendientesDe(c) !== 1 ? "s" : ""} pendiente{pendientesDe(c) !== 1 ? "s" : ""} ·{" "}
                            {c.en_linea ? "en línea" : "sin señal"}
                          </p>
                          {c.actualizado_en && (
                            <p className="text-[11px] text-slate-400">Última señal {haceCuanto(c.actualizado_en)}</p>
                          )}
                        </div>
                      </button>
                    </li>
                  );
                })}
              </ul>
            </SectionCard>
          </div>

          <div className="flex-1 overflow-hidden rounded-xl border border-slate-200">
            <MapaFlota conductores={conductoresVisibles} seleccionado={seleccionado} mostrar={filtroCapa} />
          </div>
        </div>
      )}
    </div>
  );
}
