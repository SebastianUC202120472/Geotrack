import { useEffect, useState } from "react";
import { RefreshCw, Truck, CircleCheck, CircleX, Clock, Building2, Loader2 } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import { EstadoBadge } from "../components/ui/Badge";
import { obtenerFlota, obtenerSeguimientoClientes } from "../services/api";

// Seguimiento de PEDIDOS con dos vistas (pestañas):
//  - "Por ruta": avance de cada ruta (CUS-33, /dashboard/flota).
//  - "Por cliente": repartos agregados por empresa (/dashboard/clientes).
// (El mapa con la ubicación de los conductores vive en "Seguimiento de Conductores".)
const PESTANAS = [
  { id: "ruta", label: "Por ruta" },
  { id: "cliente", label: "Por cliente" },
];

export default function Seguimiento() {
  const [tab, setTab] = useState("ruta");
  const [rutas, setRutas] = useState([]);
  const [clientes, setClientes] = useState([]);
  const [cargando, setCargando] = useState(true);

  // Carga los datos de la pestaña indicada (por defecto, la activa).
  const cargar = async (cual = tab) => {
    setCargando(true);
    try {
      if (cual === "ruta") {
        const data = await obtenerFlota();
        setRutas(data.rutas || []);
      } else {
        setClientes(await obtenerSeguimientoClientes());
      }
    } catch (err) {
      console.error("No se pudo cargar el seguimiento:", err.message);
    } finally {
      setCargando(false);
    }
  };

  // Recarga al cambiar de pestaña.
  useEffect(() => {
    cargar(tab);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab]);

  return (
    <div className="space-y-6 p-6 lg:p-8 animate-fade-in">
      <PageHeader titulo="Seguimiento de Flota" subtitulo="Avance de las operaciones de reparto.">
        <Button variant="secondary" icon={RefreshCw} onClick={() => cargar(tab)}>Actualizar</Button>
      </PageHeader>

      {/* Pestañas */}
      <div className="inline-flex rounded-xl bg-slate-100 p-1">
        {PESTANAS.map((p) => (
          <button
            key={p.id}
            onClick={() => setTab(p.id)}
            className={`rounded-lg px-4 py-2 text-sm font-semibold transition-colors ${
              tab === p.id ? "bg-white text-brand-700 shadow-sm" : "text-slate-500 hover:text-slate-700"
            }`}
          >
            {p.label}
          </button>
        ))}
      </div>

      {cargando ? (
        <Card>
          <p className="flex justify-center py-10 text-slate-400">
            <Loader2 className="animate-spin" size={22} />
          </p>
        </Card>
      ) : tab === "ruta" ? (
        <VistaRutas rutas={rutas} />
      ) : (
        <VistaClientes clientes={clientes} />
      )}
    </div>
  );
}

// --- Vista por ruta (avance de cada ruta) ---
function VistaRutas({ rutas }) {
  if (rutas.length === 0) {
    return (
      <Card>
        <div className="py-12 text-center text-sm text-slate-400">
          <Truck className="mx-auto mb-3 opacity-40" size={36} />
          <p>No hay rutas en operación todavía. Asigna un bloque de pedidos para verlas aquí.</p>
        </div>
      </Card>
    );
  }
  return (
    <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
      {rutas.map((r, i) => (
        <div key={r.ruta_id} style={{ animationDelay: `${i * 40}ms` }} className="animate-fade-up">
          <Card hover>
            <div className="mb-4 flex items-start justify-between">
              <div>
                <h3 className="font-semibold text-slate-900">{r.nombre}</h3>
                <p className="text-sm text-slate-500">{r.vehiculo_placa || "Sin vehículo"}</p>
              </div>
              <EstadoBadge estado={r.estado} />
            </div>

            <div className="mb-4">
              <div className="mb-1 flex justify-between text-sm">
                <span className="text-slate-500">Avance</span>
                <span className="font-semibold text-slate-700 nums">{Math.round(r.avance_porcentaje)}%</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                <div className="h-full rounded-full bg-brand-600 transition-all" style={{ width: `${r.avance_porcentaje}%` }} />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-2 text-center">
              <Contador icon={CircleCheck} color="text-success" valor={r.entregadas} etiqueta="Entregadas" />
              <Contador icon={CircleX} color="text-danger" valor={r.fallidas} etiqueta="Fallidas" />
              <Contador icon={Clock} color="text-warning" valor={r.pendientes} etiqueta="Pendientes" />
            </div>
          </Card>
        </div>
      ))}
    </div>
  );
}

function Contador({ icon: Icon, color, valor, etiqueta }) {
  return (
    <div className="rounded-xl bg-slate-50 py-3">
      <Icon className={`mx-auto ${color}`} size={18} />
      <p className="mt-1 text-lg font-bold text-slate-800 nums">{valor}</p>
      <p className="text-xs text-slate-400">{etiqueta}</p>
    </div>
  );
}

// --- Vista por cliente (repartos agregados por empresa) ---
function VistaClientes({ clientes }) {
  if (clientes.length === 0) {
    return (
      <Card>
        <div className="py-12 text-center text-sm text-slate-400">
          <Building2 className="mx-auto mb-3 opacity-40" size={36} />
          <p>No hay pedidos de clientes todavía.</p>
        </div>
      </Card>
    );
  }
  return (
    <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
      {clientes.map((c, i) => (
        <div key={c.cliente} style={{ animationDelay: `${i * 40}ms` }} className="animate-fade-up">
          <ClienteCard c={c} />
        </div>
      ))}
    </div>
  );
}

const MINI_DOT = { success: "bg-success", info: "bg-info", warning: "bg-warning", danger: "bg-danger" };

// Conteo de un grupo dentro de la tarjeta del cliente (color + número + etiqueta).
function Mini({ tono, valor, etiqueta }) {
  return (
    <div className="flex items-center gap-2 rounded-xl bg-slate-50 px-3 py-2">
      <span className={`h-2 w-2 shrink-0 rounded-full ${MINI_DOT[tono]}`} />
      <span className="text-lg font-bold text-slate-800 nums">{valor}</span>
      <span className="text-xs text-slate-400">{etiqueta}</span>
    </div>
  );
}

function ClienteCard({ c }) {
  const avance = c.total ? Math.round((c.entregados / c.total) * 100) : 0;
  return (
    <Card hover>
      <div className="mb-4 flex items-start justify-between gap-2">
        <div className="flex min-w-0 items-center gap-2">
          <span className="shrink-0 rounded-xl bg-brand-50 p-2 text-brand-600">
            <Building2 size={18} />
          </span>
          <h3 className="truncate font-semibold text-slate-900" title={c.cliente}>{c.cliente}</h3>
        </div>
        <span className="shrink-0 text-sm text-slate-400 nums">{c.total}</span>
      </div>

      <div className="mb-4">
        <div className="mb-1 flex justify-between text-sm">
          <span className="text-slate-500">Entregado</span>
          <span className="font-semibold text-slate-700 nums">{avance}%</span>
        </div>
        <div className="h-2 overflow-hidden rounded-full bg-slate-100">
          <div className="h-full rounded-full bg-success transition-all" style={{ width: `${avance}%` }} />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <Mini tono="success" valor={c.entregados} etiqueta="Entregados" />
        <Mini tono="info" valor={c.en_proceso} etiqueta="En proceso" />
        <Mini tono="warning" valor={c.pendientes} etiqueta="Pendientes" />
        <Mini tono="danger" valor={c.fallidos} etiqueta="Fallidos" />
      </div>
    </Card>
  );
}
