import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { RefreshCw, MapPinned, Clock, Truck, ChevronRight, PackageSearch } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import StatCard from "../components/ui/StatCard";
import SectionCard from "../components/ui/SectionCard";
import EmptyState from "../components/ui/EmptyState";
import Skeleton from "../components/ui/Skeleton";
import Button from "../components/ui/Button";
import { listarPedidos } from "../services/api";

// Agrupa los pedidos por distrito y, dentro de cada uno, cuenta pendientes y
// asignados. Solo interesan las zonas con trabajo por gestionar.
// Entrada: pedidos (array con `distrito` y `estado`).
// Salida: array de zonas { distrito, pendientes, asignados } con al menos un
// pendiente o asignado, ordenadas por la mayor cantidad de esos dos.
function agruparZonas(pedidos) {
  const mapa = new Map();
  for (const p of pedidos) {
    const clave = p.distrito || "";
    if (!mapa.has(clave)) mapa.set(clave, { distrito: clave, pendientes: 0, asignados: 0 });
    const z = mapa.get(clave);
    if (p.estado === "LISTO_PARA_ENVIO") z.pendientes++;
    else if (p.estado === "ASIGNADO") z.asignados++;
  }
  return [...mapa.values()]
    .filter((z) => z.pendientes > 0 || z.asignados > 0)
    .sort((a, b) => b.pendientes + b.asignados - (a.pendientes + a.asignados));
}

// Pastilla de conteo clicable para cada estado de zona (pendiente / asignado).
// Entrada: tono ("warning"|"info"), label, valor (number), onClick.
function PildoraEstado({ tono, label, valor, onClick }) {
  const estilos = {
    warning: {
      contenedor: "bg-warning-soft hover:bg-warning/20 disabled:opacity-50 disabled:cursor-default",
      punto: "bg-warning",
      numero: "text-warning-strong",
    },
    info: {
      contenedor: "bg-info-soft hover:bg-info/20 disabled:opacity-50 disabled:cursor-default",
      punto: "bg-info",
      numero: "text-info-strong",
    },
  };
  const t = estilos[tono];
  return (
    <button
      onClick={onClick}
      disabled={!valor}
      className={`flex flex-1 flex-col items-center gap-1 rounded-xl px-3 py-2.5 text-center transition-colors ${t.contenedor}`}
    >
      <span className={`text-2xl font-bold nums ${t.numero}`}>{valor}</span>
      <span className="flex items-center gap-1.5 text-xs font-medium text-slate-500">
        <span className={`h-1.5 w-1.5 rounded-full ${t.punto}`} />
        {label}
      </span>
    </button>
  );
}

// Tarjeta de zona individual con "Confianza cálida": cabecera con icono de pin,
// nombre del distrito, total de pedidos gestionados, y pastillas de estado clicables.
// Entrada: zona { distrito, pendientes, asignados }, irAPedidos (fn navegación).
function ZonaCard({ zona, irAPedidos, indice }) {
  const total = zona.pendientes + zona.asignados;
  return (
    <article
      className="animate-fade-up rounded-card border border-warm-200 bg-white shadow-card transition-all duration-200 hover:-translate-y-0.5 hover:shadow-card-hover"
      style={{ animationDelay: `${indice * 60}ms` }}
    >
      {/* Cabecera: zona + total clicable */}
      <button
        onClick={() => irAPedidos(zona.distrito, null)}
        className="flex w-full items-center gap-3 px-4 py-4 text-left"
      >
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-50 text-brand-600">
          <MapPinned size={20} />
        </span>
        <div className="flex-1 min-w-0">
          <h3 className="truncate font-semibold text-slate-800">
            {zona.distrito || "Sin distrito"}
          </h3>
          <p className="text-xs text-slate-400">
            {total} pedido{total !== 1 ? "s" : ""} por gestionar
          </p>
        </div>
        <ChevronRight size={16} className="shrink-0 text-slate-300" />
      </button>

      {/* Separador sutil */}
      <div className="mx-4 border-t border-warm-200" />

      {/* Pastillas de estado */}
      <div className="flex gap-2 p-3">
        <PildoraEstado
          tono="warning"
          label="Listo p/envío"
          valor={zona.pendientes}
          onClick={() => irAPedidos(zona.distrito, "LISTO_PARA_ENVIO")}
        />
        <PildoraEstado
          tono="info"
          label="Asignados"
          valor={zona.asignados}
          onClick={() => irAPedidos(zona.distrito, "ASIGNADO")}
        />
      </div>
    </article>
  );
}

// Silueta de carga para la cuadrícula de zonas (3 tarjetas placeholder).
function EsqueletoZonas() {
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      {[0, 1, 2].map((i) => (
        <div key={i} className="rounded-card border border-warm-200 bg-white p-4 shadow-card">
          <div className="flex items-center gap-3">
            <Skeleton className="h-10 w-10" rounded="rounded-xl" />
            <div className="flex-1 space-y-2">
              <Skeleton className="h-4 w-32" />
              <Skeleton className="h-3 w-20" />
            </div>
          </div>
          <div className="mt-3 flex gap-2">
            <Skeleton className="h-14 flex-1" rounded="rounded-xl" />
            <Skeleton className="h-14 flex-1" rounded="rounded-xl" />
          </div>
        </div>
      ))}
    </div>
  );
}

export default function AgrupacionZonas() {
  const navigate = useNavigate();
  const [pedidos, setPedidos] = useState([]);
  const [cargando, setCargando] = useState(true);

  const cargar = async () => {
    setCargando(true);
    try {
      setPedidos(await listarPedidos());
    } catch (err) {
      console.error("Error al cargar zonas:", err.message);
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    cargar();
  }, []);

  const zonas = useMemo(() => agruparZonas(pedidos), [pedidos]);
  const totalPendientes = zonas.reduce((acc, z) => acc + z.pendientes, 0);
  const totalAsignados = zonas.reduce((acc, z) => acc + z.asignados, 0);

  // Navega al listado de Pedidos filtrado por distrito (y opcionalmente estado).
  const irAPedidos = (distrito, estado) => {
    const params = new URLSearchParams();
    if (distrito) params.set("distrito", distrito);
    if (estado) params.set("estado", estado);
    navigate(`/pedidos?${params.toString()}`);
  };

  return (
    <div className="space-y-6 p-6 lg:p-8 animate-fade-in">
      <PageHeader
        titulo="Agrupación por Zonas"
        subtitulo="Zonas con pedidos pendientes o asignados, listas para enrutar."
      >
        <Button variant="secondary" icon={RefreshCw} onClick={cargar}>Actualizar</Button>
      </PageHeader>

      {/* KPIs resumen */}
      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard
          label="Zonas activas"
          value={zonas.length}
          icon={MapPinned}
          tone="brand"
          hint="Con pendientes o asignados"
        />
        <StatCard
          label="Listo p/envío"
          value={totalPendientes}
          icon={Clock}
          tone="warning"
          hint="Por asignar a una ruta"
        />
        <StatCard
          label="Asignados"
          value={totalAsignados}
          icon={Truck}
          tone="info"
          hint="Ya en una ruta"
        />
      </div>

      {/* Cuadrícula de zonas */}
      <SectionCard
        title="Zonas operativas detectadas"
        subtitle="Haz clic en un conteo para ir al listado filtrado"
      >
        {cargando ? (
          <EsqueletoZonas />
        ) : zonas.length === 0 ? (
          <EmptyState
            icon={PackageSearch}
            title="Sin zonas con pedidos activos"
            description="No hay zonas con pedidos pendientes o asignados. Importa o asigna pedidos para verlas aquí."
          />
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {zonas.map((z, i) => (
              <ZonaCard
                key={z.distrito || "sin-distrito"}
                zona={z}
                irAPedidos={irAPedidos}
                indice={i}
              />
            ))}
          </div>
        )}
      </SectionCard>
    </div>
  );
}
