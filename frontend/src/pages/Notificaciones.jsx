import { useEffect, useMemo, useState } from "react";
import { Bell, BellRing } from "lucide-react";
import { useNavigate } from "react-router-dom";
import PageHeader from "../components/ui/PageHeader";
import KpiCard from "../components/ui/KpiCard";
import SectionCard from "../components/ui/SectionCard";
import EmptyState from "../components/ui/EmptyState";
import { obtenerNotificaciones } from "../services/api";

// Devuelve una cadena legible del tiempo transcurrido desde una fecha ISO.
// (Mismo formato que la campana del sidebar.) Entrada: fechaIso. Salida: "hace X…".
function tiempoRelativo(fechaIso) {
  const diff = Date.now() - new Date(fechaIso).getTime();
  const min = Math.floor(diff / 60000);
  if (min < 1) return "ahora mismo";
  if (min < 60) return `hace ${min} min`;
  const hrs = Math.floor(min / 60);
  if (hrs < 24) return `hace ${hrs} h`;
  const dias = Math.floor(hrs / 24);
  return `hace ${dias} día${dias > 1 ? "s" : ""}`;
}

// Fecha absoluta corta (es-PE) para el detalle de cada ítem.
const fmt = (f) => (f ? new Date(f).toLocaleString("es-PE", { dateStyle: "short", timeStyle: "short" }) : "—");

// Página de historial completo de notificaciones (pide limite=200) con un filtro
// simple (Todas / No vistas) y la lista cronológica (recientes primero).
export default function Notificaciones() {
  const navigate = useNavigate();
  const [items, setItems] = useState([]);
  const [noVistas, setNoVistas] = useState(0);
  const [cargando, setCargando] = useState(true);
  const [filtro, setFiltro] = useState("todas"); // "todas" | "no_vistas"

  // Carga el historial completo (limite=200). setState en callbacks de promesa.
  useEffect(() => {
    let activo = true;
    obtenerNotificaciones(200)
      .then((d) => {
        if (!activo) return;
        setItems(Array.isArray(d?.items) ? d.items : []);
        setNoVistas(d?.no_vistas ?? 0);
      })
      .catch(() => {})
      .finally(() => activo && setCargando(false));
    return () => { activo = false; };
  }, []);

  // Aplica el filtro Todas / No vistas sobre la lista cargada.
  const filtrados = useMemo(
    () => (filtro === "no_vistas" ? items.filter((i) => i.visto_en === null) : items),
    [items, filtro],
  );

  // Navega a la ruta asociada a la notificación (si la trae).
  const irA = (ruta) => { if (ruta) navigate(ruta); };

  const botonFiltro = (valor, etiqueta) => (
    <button
      onClick={() => setFiltro(valor)}
      className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
        filtro === valor ? "bg-brand-600 text-white" : "bg-white text-slate-600 hover:bg-slate-50 border border-slate-200"
      }`}
    >
      {etiqueta}
    </button>
  );

  return (
    <div className="space-y-6 p-6 lg:p-8 animate-fade-in">
      <PageHeader titulo="Notificaciones" subtitulo="Historial completo de avisos del sistema (recientes primero)." />

      <div className="grid grid-cols-2 gap-4 sm:max-w-md animate-fade-up">
        <KpiCard label="Total" value={items.length} icon={Bell} tone="brand" />
        <KpiCard label="No vistas" value={noVistas} icon={BellRing} tone={noVistas > 0 ? "warning" : "info"} />
      </div>

      <SectionCard className="animate-fade-up" title="Avisos"
        action={<div className="flex gap-2">{botonFiltro("todas", "Todas")}{botonFiltro("no_vistas", "No vistas")}</div>}
      >
        {cargando ? (
          <p className="py-8 text-center text-sm text-slate-500">Cargando notificaciones…</p>
        ) : filtrados.length === 0 ? (
          <EmptyState icon={Bell} title="Sin notificaciones" description="No hay avisos que coincidan con el filtro." />
        ) : (
          <ul className="-mx-5 divide-y divide-slate-100">
            {filtrados.map((item) => {
              const noVisto = item.visto_en === null;
              const clicable = !!item.ruta;
              return (
                <li key={item.id} className={noVisto ? "bg-brand-50/40" : ""}>
                  <button
                    onClick={() => irA(item.ruta)}
                    disabled={!clicable}
                    className={`flex w-full items-start gap-3 px-5 py-3.5 text-left transition-colors ${clicable ? "hover:bg-slate-50 cursor-pointer" : "cursor-default"}`}
                  >
                    <span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${noVisto ? "bg-brand-600" : "bg-slate-300"}`} aria-hidden="true" />
                    <div className="min-w-0 flex-1">
                      <p className={`text-sm font-semibold ${noVisto ? "text-slate-900" : "text-slate-700"}`}>{item.titulo}</p>
                      <p className="text-sm text-slate-500">{item.mensaje}</p>
                      <p className="mt-0.5 text-xs text-slate-400 nums">{tiempoRelativo(item.creado_en)} · {fmt(item.creado_en)}</p>
                    </div>
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </SectionCard>
    </div>
  );
}
