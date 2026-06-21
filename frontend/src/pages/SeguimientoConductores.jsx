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

const REFRESCO_MS = 15000; // el mapa se actualiza solo cada 15 s (polling)

// Colores distintos por conductor (el marcador del conductor y sus paradas comparten color).
const COLORES = ["#2563EB", "#DC2626", "#059669", "#D97706", "#7C3AED", "#DB2777", "#0891B2", "#65A30D"];

// Seguimiento de conductores en el mapa: posición en vivo de cada conductor con
// ruta activa y sus pedidos pendientes (Leaflet + OpenStreetMap).
export default function SeguimientoConductores() {
  const [ubicaciones, setUbicaciones] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [seleccionado, setSeleccionado] = useState(null); // conductor_id a centrar en el mapa

  // Carga manual (botón "Actualizar"), con indicador de carga.
  const actualizar = () => {
    setCargando(true);
    obtenerUbicacionesFlota()
      .then(setUbicaciones)
      .catch((err) => console.error("No se pudo cargar el mapa:", err.message))
      .finally(() => setCargando(false));
  };

  // Carga inicial + refresco automático cada 15 s (sin parpadeo). Los setState van
  // dentro de los callbacks de la promesa, no en el cuerpo del efecto.
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

  // Métricas derivadas del estado ya cargado (sin fetch extra).
  const totalConductores = ubicaciones.length;
  const enLinea = ubicaciones.filter((c) => c.en_linea).length;
  const sinSenal = totalConductores - enLinea;
  const totalParadas = ubicaciones.reduce((acc, c) => acc + (c.paradas?.length ?? 0), 0);
  // Conductores que declararon una incidencia y están en pausa activa.
  const pausados = ubicaciones.filter((u) => u.pausado).length;

  // A cada conductor se le asigna un color (compartido con sus paradas en el mapa).
  const conductores = ubicaciones.map((c, i) => ({ ...c, _color: COLORES[i % COLORES.length] }));

  return (
    <div className="space-y-6 p-6 lg:p-8">
      {/* Cabecera con badge "En vivo" */}
      <div className="animate-fade-up">
        <PageHeader
          titulo="Seguimiento de Conductores"
          subtitulo="Ubicación en vivo de cada conductor con ruta activa y sus pedidos pendientes."
        >
          <LiveBadge tone="success">En vivo</LiveBadge>
          <Button variant="secondary" icon={RefreshCw} onClick={actualizar}>
            Actualizar
          </Button>
        </PageHeader>
      </div>

      {/* Fila de KPIs (solo visible cuando hay datos) */}
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
          {/* Conductores pausados por incidencia activa */}
          <KpiCard
            label="Pausados"
            value={pausados}
            icon={Wrench}
            tone={pausados > 0 ? "danger" : "info"}
          />
        </div>
      )}

      {/* Cuerpo principal: panel lateral + mapa */}
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
          {/* Panel lateral: lista de conductores */}
          <div className="w-full lg:w-72 shrink-0">
            <SectionCard
              title="Conductores"
              subtitle={`${totalConductores} en ruta`}
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
                        {/* Punto del color del conductor (coincide con sus marcadores en el mapa) */}
                        <span
                          className={`mt-1 h-3 w-3 shrink-0 rounded-full border border-white shadow ${c.en_linea ? "live-dot" : ""}`}
                          style={{ backgroundColor: c._color, opacity: c.en_linea ? 1 : 0.5 }}
                          aria-hidden="true"
                        />
                        <div className="min-w-0">
                          <p className="truncate text-sm font-semibold text-slate-900">
                            {c.conductor || "Conductor"}
                          </p>
                          {/* Marca roja cuando el conductor está pausado por una incidencia */}
                          {c.pausado && (
                            <span className="inline-block rounded-full bg-danger-soft px-2 py-0.5 text-[11px] font-semibold text-danger-strong">🛠️ Pausado</span>
                          )}
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

          {/* Mapa de flota — props idénticas al original */}
          <div className="flex-1 overflow-hidden rounded-xl border border-slate-200">
            <MapaFlota conductores={conductores} seleccionado={seleccionado} />
          </div>
        </div>
      )}
    </div>
  );
}
