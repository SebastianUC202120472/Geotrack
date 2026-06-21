import { useEffect, useState } from "react";
import { AlertTriangle, Wrench, CheckCircle2, MapPin } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import SectionCard from "../components/ui/SectionCard";
import KpiCard from "../components/ui/KpiCard";
import Button from "../components/ui/Button";
import Badge from "../components/ui/Badge";
import EmptyState from "../components/ui/EmptyState";
import { listarIncidencias, resolverIncidencia } from "../services/api";

// CUS-30: gestión de incidencias de auxilio mecánico reportadas por los conductores.
export default function AuxilioMecanico() {
  const [incidencias, setIncidencias] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [resolviendo, setResolviendo] = useState(null);

  // Recarga la lista (setState en callbacks de promesa, no síncrono en el effect).
  const cargar = () => {
    listarIncidencias()
      .then(setIncidencias)
      .catch((e) => console.error("No se pudieron cargar incidencias:", e.message))
      .finally(() => setCargando(false));
  };

  useEffect(() => {
    let activo = true;
    listarIncidencias()
      .then((d) => activo && setIncidencias(d))
      .catch(() => {})
      .finally(() => activo && setCargando(false));
    const id = setInterval(cargar, 20000); // refresco silencioso
    return () => { activo = false; clearInterval(id); };
  }, []);

  const abiertas = incidencias.filter((i) => i.estado === "ABIERTA").length;
  const resueltas = incidencias.filter((i) => i.estado === "RESUELTA").length;

  // Marca una incidencia como resuelta desde el panel.
  const resolver = (id) => {
    setResolviendo(id);
    resolverIncidencia(id)
      .then(cargar)
      .catch((e) => alert(e.message))
      .finally(() => setResolviendo(null));
  };

  return (
    <div className="space-y-6 p-6 lg:p-8 animate-fade-in">
      <PageHeader
        titulo="Auxilio Mecánico"
        subtitulo="Averías reportadas por los conductores. Mientras una está abierta, su ruta queda pausada."
      />

      <div className="grid gap-4 sm:grid-cols-2 animate-fade-up">
        <KpiCard label="Abiertas" value={abiertas} tone="danger" icon={AlertTriangle} live={abiertas > 0} />
        <KpiCard label="Resueltas" value={resueltas} tone="success" icon={CheckCircle2} />
      </div>

      <SectionCard title="Incidencias" subtitle="Las abiertas aparecen primero.">
        {cargando ? (
          <p className="text-sm text-slate-400">Cargando…</p>
        ) : incidencias.length === 0 ? (
          <EmptyState icon={Wrench} title="Sin incidencias" description="No hay averías reportadas." />
        ) : (
          <ul className="divide-y divide-slate-100">
            {incidencias.map((i) => (
              <li key={i.id} className="flex flex-wrap items-center justify-between gap-3 py-3.5">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-slate-800">{i.codigo ?? `IN-${i.id}`}</span>
                    <Badge tono={i.estado === "ABIERTA" ? "danger" : "success"}>{i.estado}</Badge>
                    {i.vehiculo_placa && (
                      <span className="text-xs text-slate-500">🚚 {i.vehiculo_placa}</span>
                    )}
                  </div>
                  <p className="mt-0.5 truncate text-sm text-slate-600">
                    {i.conductor_nombre ?? "Conductor"} · {i.ruta_nombre ?? "Ruta"} · {i.descripcion || "Sin detalle"}
                  </p>
                  {i.latitud != null && i.longitud != null && (
                    <a
                      className="mt-1 inline-flex items-center gap-1 text-xs text-brand-600 hover:underline"
                      href={`https://www.google.com/maps?q=${i.latitud},${i.longitud}`}
                      target="_blank"
                      rel="noreferrer"
                    >
                      <MapPin size={13} /> Ver ubicación
                    </a>
                  )}
                </div>
                {i.estado === "ABIERTA" && (
                  <Button
                    size="sm"
                    icon={CheckCircle2}
                    disabled={resolviendo === i.id}
                    onClick={() => resolver(i.id)}
                  >
                    {resolviendo === i.id ? "Resolviendo…" : "Marcar resuelta"}
                  </Button>
                )}
              </li>
            ))}
          </ul>
        )}
      </SectionCard>
    </div>
  );
}
