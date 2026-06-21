import { useEffect, useState } from "react";
import { RefreshCw, MapPin, Users, Wifi, WifiOff } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import KpiCard from "../components/ui/KpiCard";
import SectionCard from "../components/ui/SectionCard";
import EmptyState from "../components/ui/EmptyState";
import LiveBadge from "../components/ui/LiveBadge";
import Button from "../components/ui/Button";
import MapaFlota from "../components/MapaFlota";
import { obtenerUbicacionesFlota } from "../services/api";

const REFRESCO_MS = 15000; // el mapa se actualiza solo cada 15 s (polling)

// Seguimiento de conductores en el mapa: posición en vivo de cada conductor con
// ruta activa y sus pedidos pendientes (Leaflet + OpenStreetMap).
export default function SeguimientoConductores() {
  const [ubicaciones, setUbicaciones] = useState([]);
  const [cargando, setCargando] = useState(true);

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
              <ul className="space-y-2 -mx-5 px-0">
                {ubicaciones.map((c) => (
                  <li
                    key={c.conductor_id}
                    className="flex items-start gap-3 rounded-lg px-5 py-3 transition-colors hover:bg-slate-50"
                  >
                    {/* Indicador de estado en línea */}
                    <span
                      className={`mt-1 h-2.5 w-2.5 shrink-0 rounded-full ${
                        c.en_linea ? "bg-success live-dot" : "bg-slate-300"
                      }`}
                      aria-hidden="true"
                    />
                    <div className="min-w-0">
                      <p className="truncate text-sm font-semibold text-slate-900">
                        {c.conductor || "Conductor"}
                      </p>
                      <p className="truncate text-xs text-slate-500">{c.ruta || "Sin ruta"}</p>
                      <p className="mt-0.5 text-xs text-slate-400">
                        {c.paradas?.length ?? 0} parada{(c.paradas?.length ?? 0) !== 1 ? "s" : ""}
                      </p>
                    </div>
                  </li>
                ))}
              </ul>
            </SectionCard>
          </div>

          {/* Mapa de flota — props idénticas al original */}
          <div className="flex-1 overflow-hidden rounded-xl border border-slate-200">
            <MapaFlota conductores={ubicaciones} />
          </div>
        </div>
      )}
    </div>
  );
}
