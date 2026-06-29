import { useEffect, useState } from "react";
import { RefreshCw, MapPin, Users, Wifi, WifiOff } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import KpiCard from "../components/ui/KpiCard";
import SectionCard from "../components/ui/SectionCard";
import EmptyState from "../components/ui/EmptyState";
import LiveBadge from "../components/ui/LiveBadge";
import Button from "../components/ui/Button";
import MapaFlota from "../components/MapaFlota";
import { obtenerUbicacionesRecojo } from "../services/api";

const REFRESCO_MS = 15000; // polling cada 15 s

// Colores por conductor (coinciden con sus marcadores en el mapa).
const COLORES = ["#2563EB", "#DC2626", "#059669", "#D97706", "#7C3AED", "#DB2777", "#0891B2", "#65A30D"];

// Mapa de recojos en vivo: posición de los conductores en rutas de RECOJO activas.
// Reutiliza el componente MapaFlota del admin con datos filtrados por tipo=RECOJO.
export default function MapaRecojos() {
  const [ubicaciones, setUbicaciones] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [seleccionado, setSeleccionado] = useState(null); // conductor_id centrado en el mapa

  // Carga manual con indicador de carga.
  const actualizar = () => {
    setCargando(true);
    obtenerUbicacionesRecojo()
      .then(setUbicaciones)
      .catch((err) => console.error("No se pudo cargar el mapa de recojos:", err.message))
      .finally(() => setCargando(false));
  };

  // Carga inicial + refresco automático cada 15 s. Los setState van en los callbacks
  // de la promesa (no en el cuerpo del efecto) para no activar la regla de lint.
  useEffect(() => {
    let activo = true;
    const traer = () =>
      obtenerUbicacionesRecojo()
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

  // Métricas derivadas del estado ya cargado.
  const totalConductores = ubicaciones.length;
  const enLinea = ubicaciones.filter((c) => c.en_linea).length;
  const sinSenal = totalConductores - enLinea;
  const totalParadas = ubicaciones.reduce((acc, c) => acc + (c.paradas?.length ?? 0), 0);

  // Asignar color por conductor.
  const conductores = ubicaciones.map((c, i) => ({ ...c, _color: COLORES[i % COLORES.length] }));

  return (
    <div className="space-y-6 p-6 lg:p-8">
      {/* Cabecera con badge en vivo */}
      <div className="animate-fade-up">
        <PageHeader
          titulo="Mapa de Recojos"
          subtitulo="Ubicación en vivo de los conductores asignados a rutas de recojo activas."
        >
          <LiveBadge tone="success">En vivo</LiveBadge>
          <Button variant="secondary" icon={RefreshCw} onClick={actualizar}>
            Actualizar
          </Button>
        </PageHeader>
      </div>

      {/* KPIs (solo si hay datos) */}
      {!cargando && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 animate-fade-up">
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
        </div>
      )}

      {/* Cuerpo: spinner, estado vacío o mapa */}
      {cargando ? (
        <div className="animate-fade-up rounded-xl border border-slate-200 bg-white shadow-card p-10 text-center text-sm text-slate-500">
          Cargando mapa…
        </div>
      ) : ubicaciones.length === 0 ? (
        <div className="animate-fade-up">
          <SectionCard>
            <EmptyState
              icon={MapPin}
              title="Sin conductores en recojo"
              description="No hay conductores con ruta de recojo activa enviando su ubicación ahora mismo."
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
          {/* Panel lateral: lista de conductores */}
          <div className="w-full lg:w-72 shrink-0">
            <SectionCard
              title="Conductores"
              subtitle={`${totalConductores} en recojo`}
              className="h-full"
            >
              <ul className="space-y-1 -mx-5 px-0">
                {conductores.map((c) => {
                  const activo = seleccionado === c.conductor_id;
                  return (
                    <li key={c.conductor_id}>
                      <button
                        type="button"
                        onClick={() => setSeleccionado(c.conductor_id)}
                        className={`flex w-full items-start gap-3 rounded-lg px-5 py-3 text-left transition-colors ${
                          activo ? "bg-brand-50" : "hover:bg-slate-50"
                        }`}
                      >
                        {/* Punto del color del conductor */}
                        <span
                          className={`mt-1 h-3 w-3 shrink-0 rounded-full border border-white shadow ${c.en_linea ? "live-dot" : ""}`}
                          style={{ backgroundColor: c._color, opacity: c.en_linea ? 1 : 0.5 }}
                          aria-hidden="true"
                        />
                        <div className="min-w-0">
                          <p className="truncate text-sm font-semibold text-slate-900">
                            {c.conductor || "Conductor"}
                          </p>
                          <p className="truncate text-xs text-slate-500">{c.ruta || "Sin ruta"}</p>
                          <p className="mt-0.5 text-xs text-slate-400">
                            {c.paradas?.length ?? 0} parada{(c.paradas?.length ?? 0) !== 1 ? "s" : ""} ·{" "}
                            {c.en_linea ? "en línea" : "sin señal"}
                          </p>
                        </div>
                      </button>
                    </li>
                  );
                })}
              </ul>
            </SectionCard>
          </div>

          {/* Mapa de flota reutilizado */}
          <div className="flex-1 overflow-hidden rounded-xl border border-slate-200">
            <MapaFlota conductores={conductores} seleccionado={seleccionado} />
          </div>
        </div>
      )}
    </div>
  );
}
