import { useEffect, useState } from "react";
import { RefreshCw, Truck, CircleCheck, CircleX, Clock, Building2, Loader2, Route, FileSpreadsheet, ListOrdered, ArrowUp, ArrowDown, Trash2, X, AlertCircle } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import Card from "../components/ui/Card";
import SectionCard from "../components/ui/SectionCard";
import KpiCard from "../components/ui/KpiCard";
import EmptyState from "../components/ui/EmptyState";
import LiveBadge from "../components/ui/LiveBadge";
import Button from "../components/ui/Button";
import Modal from "../components/ui/Modal";
import { EstadoBadge } from "../components/ui/Badge";
import { obtenerFlota, obtenerSeguimientoClientes, generarLiquidacion, descargarLiquidacion,
  listarParadasRuta, reordenarParadas, quitarParada, descargarManifiesto } from "../services/api";

// Seguimiento de PEDIDOS con dos vistas (pestañas):
//  - "Por ruta": avance de cada ruta (CUS-33, /dashboard/flota).
//  - "Por cliente": repartos agregados por empresa (/dashboard/clientes).
// (El mapa con la ubicación de los conductores vive en "Seguimiento de Conductores".)
const PESTANAS = [
  { id: "ruta", label: "Por ruta", icon: Truck },
  { id: "cliente", label: "Por cliente", icon: Building2 },
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

  // Métricas de KPIs calculadas desde los datos ya cargados (sin fetch extra).
  const kpisRuta = {
    totalRutas: rutas.length,
    totalEntregadas: rutas.reduce((s, r) => s + (r.entregadas || 0), 0),
    totalFallidas: rutas.reduce((s, r) => s + (r.fallidas || 0), 0),
    totalPendientes: rutas.reduce((s, r) => s + (r.pendientes || 0), 0),
  };

  const kpisCliente = {
    totalClientes: clientes.length,
    totalEntregados: clientes.reduce((s, c) => s + (c.entregados || 0), 0),
    totalFallidos: clientes.reduce((s, c) => s + (c.fallidos || 0), 0),
    totalPendientes: clientes.reduce((s, c) => s + (c.pendientes || 0), 0),
  };

  // KPI actual según la pestaña visible.
  const kpis =
    tab === "ruta"
      ? [
          { label: "Rutas activas", value: kpisRuta.totalRutas, icon: Route, tone: "brand", live: true },
          { label: "Entregadas", value: kpisRuta.totalEntregadas, icon: CircleCheck, tone: "success" },
          { label: "Pendientes", value: kpisRuta.totalPendientes, icon: Clock, tone: "warning" },
          { label: "Fallidas", value: kpisRuta.totalFallidas, icon: CircleX, tone: "danger" },
        ]
      : [
          { label: "Clientes", value: kpisCliente.totalClientes, icon: Building2, tone: "brand", live: true },
          { label: "Entregados", value: kpisCliente.totalEntregados, icon: CircleCheck, tone: "success" },
          { label: "Pendientes", value: kpisCliente.totalPendientes, icon: Clock, tone: "warning" },
          { label: "Fallidos", value: kpisCliente.totalFallidos, icon: CircleX, tone: "danger" },
        ];

  return (
    <div className="space-y-6 p-6 lg:p-8">
      {/* Cabecera */}
      <div className="animate-fade-up">
        <PageHeader
          titulo="Seguimiento"
          subtitulo="Avance de las operaciones de reparto por ruta y por cliente."
        >
          <LiveBadge tone="success" pulse>
            En vivo
          </LiveBadge>
          <Button variant="secondary" icon={RefreshCw} onClick={() => cargar(tab)}>
            Actualizar
          </Button>
        </PageHeader>
      </div>

      {/* Fila de KPIs (solo cuando no está cargando) */}
      {!cargando && (
        <div
          className="grid grid-cols-2 gap-4 sm:grid-cols-4 animate-fade-up"
          style={{ animationDelay: "60ms" }}
        >
          {kpis.map((k) => (
            <KpiCard
              key={k.label}
              label={k.label}
              value={k.value}
              icon={k.icon}
              tone={k.tone}
              live={k.live}
            />
          ))}
        </div>
      )}

      {/* Selector de pestañas moderno */}
      <div className="animate-fade-up" style={{ animationDelay: "120ms" }}>
        <div className="inline-flex items-center gap-1 rounded-2xl border border-warm-200 bg-white p-1 shadow-card">
          {PESTANAS.map((p) => {
            const Ico = p.icon;
            const activo = tab === p.id;
            return (
              <button
                key={p.id}
                onClick={() => setTab(p.id)}
                className={`inline-flex items-center gap-2 rounded-xl px-5 py-2 text-sm font-semibold transition-all duration-200 ${
                  activo
                    ? "bg-brand-600 text-white shadow-sm"
                    : "text-slate-500 hover:bg-slate-50 hover:text-slate-800"
                }`}
              >
                <Ico size={15} />
                {p.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Contenido principal */}
      <div className="animate-fade-up" style={{ animationDelay: "180ms" }}>
        {cargando ? (
          <SectionCard>
            <div className="flex justify-center py-12 text-slate-400">
              <Loader2 className="animate-spin" size={24} />
            </div>
          </SectionCard>
        ) : tab === "ruta" ? (
          <VistaRutas rutas={rutas} onCambios={() => cargar("ruta")} />
        ) : (
          <VistaClientes clientes={clientes} />
        )}
      </div>
    </div>
  );
}

// --- Vista por ruta (avance de cada ruta) ---
function VistaRutas({ rutas, onCambios }) {
  const [editando, setEditando] = useState(null); // ruta cuyas paradas se editan (CUS-20)

  if (rutas.length === 0) {
    return (
      <SectionCard title="Rutas en operación">
        <EmptyState
          icon={Truck}
          title="Sin rutas activas"
          description="Asigna un bloque de pedidos para ver el avance de cada ruta aquí."
        />
      </SectionCard>
    );
  }
  return (
    <SectionCard title="Rutas en operación" subtitle={`${rutas.length} ruta${rutas.length !== 1 ? "s" : ""} activa${rutas.length !== 1 ? "s" : ""}`}>
      <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
        {rutas.map((r, i) => (
          <div key={r.ruta_id} style={{ animationDelay: `${i * 40}ms` }} className="animate-fade-up">
            <Card hover>
              <div className="mb-4 flex items-start justify-between">
                <div>
                  <h3 className="font-semibold text-slate-900">{r.nombre}</h3>
                  <p className="text-sm text-slate-500">{r.conductor_nombre || "Sin conductor"}</p>
                </div>
                <EstadoBadge estado={r.estado} />
              </div>

              <div className="mb-4">
                <div className="mb-1 flex justify-between text-sm">
                  <span className="text-slate-500">Avance</span>
                  <span className="font-semibold text-slate-700 nums">
                    {Math.round(r.avance_porcentaje)}%
                  </span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                  <div
                    className="h-full rounded-full bg-brand-600 transition-all"
                    style={{ width: `${r.avance_porcentaje}%` }}
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-2 text-center">
                <Contador icon={CircleCheck} color="text-success" valor={r.entregadas} etiqueta="Entregadas" />
                <Contador icon={CircleX} color="text-danger" valor={r.fallidas} etiqueta="Fallidas" />
                <Contador icon={Clock} color="text-warning" valor={r.pendientes} etiqueta="Pendientes" />
              </div>

              {/* CUS-20 / CUS-21: editar paradas y descargar manifiesto */}
              <div className="mt-4 flex gap-2">
                <Button variant="secondary" size="sm" icon={ListOrdered} block onClick={() => setEditando(r)}>Editar paradas</Button>
                <Button variant="ghost" size="sm" icon={FileSpreadsheet} onClick={() => descargarManifiesto(r.ruta_id, `manifiesto_${r.nombre}.xlsx`)}>Manifiesto</Button>
              </div>
            </Card>
          </div>
        ))}
      </div>

      <Modal open={!!editando} onClose={() => setEditando(null)} variant="center">
        {editando && (
          <EditarParadas ruta={editando} onCerrar={() => setEditando(null)} onCambios={() => { onCambios && onCambios(); }} />
        )}
      </Modal>
    </SectionCard>
  );
}

// Editor de paradas de una ruta (CUS-20): reordenar (subir/bajar) y quitar.
function EditarParadas({ ruta, onCerrar, onCambios }) {
  const [paradas, setParadas] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [guardando, setGuardando] = useState(false);
  const [aviso, setAviso] = useState(null);

  useEffect(() => {
    let activo = true;
    listarParadasRuta(ruta.ruta_id)
      .then((d) => activo && setParadas(d.paradas || []))
      .catch((err) => activo && setAviso({ texto: err.message }))
      .finally(() => activo && setCargando(false));
    return () => { activo = false; };
  }, [ruta.ruta_id]);

  // Mueve una parada arriba/abajo en la lista local (se persiste al guardar el orden).
  const mover = (idx, delta) => {
    const j = idx + delta;
    if (j < 0 || j >= paradas.length) return;
    const copia = [...paradas];
    [copia[idx], copia[j]] = [copia[j], copia[idx]];
    setParadas(copia);
  };

  const guardarOrden = async () => {
    setGuardando(true); setAviso(null);
    try {
      await reordenarParadas(ruta.ruta_id, paradas.map((p) => p.pedido_id));
      onCambios();
      onCerrar();
    } catch (err) { setAviso({ texto: err.message }); setGuardando(false); }
  };

  const quitar = async (pedidoId) => {
    setAviso(null);
    try {
      await quitarParada(ruta.ruta_id, pedidoId);
      setParadas((ps) => ps.filter((p) => p.pedido_id !== pedidoId));
      onCambios();
    } catch (err) { setAviso({ texto: err.message }); }
  };

  return (
    <>
      <div className="flex items-start justify-between">
        <div>
          <h2 className="font-bold text-slate-900">Paradas · {ruta.nombre}</h2>
          <p className="text-sm text-slate-500">Reordena (↑↓) o quita una parada.</p>
        </div>
        <button onClick={onCerrar} aria-label="Cerrar" className="rounded-lg p-2 text-slate-500 hover:bg-slate-100"><X size={20} /></button>
      </div>

      {aviso && (
        <div className="mt-4 flex items-center gap-2 rounded-xl bg-danger-soft px-3.5 py-3 text-sm text-danger-strong">
          <AlertCircle size={18} /> <span>{aviso.texto}</span>
        </div>
      )}

      <div className="mt-4 max-h-80 overflow-y-auto">
        {cargando ? (
          <p className="py-6 text-center text-sm text-slate-400">Cargando…</p>
        ) : paradas.length === 0 ? (
          <p className="py-6 text-center text-sm text-slate-400">Esta ruta no tiene paradas.</p>
        ) : (
          <ul className="space-y-2">
            {paradas.map((p, idx) => (
              <li key={p.pedido_id} className="flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2">
                <span className="w-6 shrink-0 text-center text-sm font-bold text-brand-600 nums">{idx + 1}</span>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-slate-700">{p.nombre_destinatario || p.codigo || `Pedido ${p.pedido_id}`}</p>
                  <p className="truncate text-xs text-slate-400">{p.direccion_destino}</p>
                </div>
                <button onClick={() => mover(idx, -1)} disabled={idx === 0} className="rounded p-1 text-slate-500 hover:bg-slate-100 disabled:opacity-30"><ArrowUp size={16} /></button>
                <button onClick={() => mover(idx, 1)} disabled={idx === paradas.length - 1} className="rounded p-1 text-slate-500 hover:bg-slate-100 disabled:opacity-30"><ArrowDown size={16} /></button>
                <button onClick={() => quitar(p.pedido_id)} className="rounded p-1 text-danger hover:bg-danger-soft"><Trash2 size={16} /></button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="mt-4 flex gap-2">
        <Button variant="secondary" block onClick={onCerrar} disabled={guardando}>Cerrar</Button>
        <Button block onClick={guardarOrden} disabled={guardando || paradas.length === 0}>{guardando ? "Guardando…" : "Guardar orden"}</Button>
      </div>
    </>
  );
}

// Minibloque de conteo dentro de la tarjeta de ruta (icono + número + etiqueta).
// Entrada: icon (componente lucide), color (clase css), valor (number), etiqueta (string).
function Contador({ icon: Icon, color, valor, etiqueta }) {
  return (
    <div className="rounded-xl bg-slate-50 py-3 transition-colors hover:bg-brand-50">
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
      <SectionCard title="Clientes">
        <EmptyState
          icon={Building2}
          title="Sin pedidos de clientes"
          description="Los repartos agrupados por empresa aparecerán aquí."
        />
      </SectionCard>
    );
  }
  return (
    <SectionCard
      title="Por cliente"
      subtitle={`${clientes.length} empresa${clientes.length !== 1 ? "s" : ""} con pedidos activos`}
    >
      <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
        {clientes.map((c, i) => (
          <div key={c.cliente} style={{ animationDelay: `${i * 40}ms` }} className="animate-fade-up">
            <ClienteCard c={c} />
          </div>
        ))}
      </div>
    </SectionCard>
  );
}

const MINI_DOT = { success: "bg-success", info: "bg-info", warning: "bg-warning", danger: "bg-danger" };

// Conteo de un grupo dentro de la tarjeta del cliente (color + número + etiqueta).
// Entrada: tono (string clave de MINI_DOT), valor (number), etiqueta (string).
function Mini({ tono, valor, etiqueta }) {
  return (
    <div className="flex items-center gap-2 rounded-xl bg-slate-50 px-3 py-2 transition-colors hover:bg-brand-50">
      <span className={`h-2 w-2 shrink-0 rounded-full ${MINI_DOT[tono]}`} />
      <span className="text-lg font-bold text-slate-800 nums">{valor}</span>
      <span className="text-xs text-slate-400">{etiqueta}</span>
    </div>
  );
}

// Tarjeta individual de empresa con barra de progreso y desglose de estados.
// Entrada: c (objeto cliente con campos total, entregados, en_proceso, pendientes, fallidos).
function ClienteCard({ c }) {
  const avance = c.total ? Math.round((c.entregados / c.total) * 100) : 0;
  const [generando, setGenerando] = useState(false);
  const [error, setError] = useState(null);

  // CUS-36: genera la liquidación del cliente en el backend (la guarda en la BD) y
  // descarga el .xlsx resultante (autenticado) en el navegador.
  const descargar = async () => {
    setGenerando(true);
    setError(null);
    try {
      const res = await generarLiquidacion({ cliente: c.cliente });
      await descargarLiquidacion(res.descarga_url, res.archivo);
    } catch (err) {
      setError(err.message);
    } finally {
      setGenerando(false);
    }
  };

  return (
    <Card hover>
      <div className="mb-4 flex items-start justify-between gap-2">
        <div className="flex min-w-0 items-center gap-2">
          <span className="shrink-0 rounded-xl bg-brand-50 p-2 text-brand-600">
            <Building2 size={18} />
          </span>
          <h3 className="truncate font-semibold text-slate-900" title={c.cliente}>
            {c.cliente}
          </h3>
        </div>
        <span className="shrink-0 rounded-full bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-500 nums">
          {c.total}
        </span>
      </div>

      <div className="mb-4">
        <div className="mb-1 flex justify-between text-sm">
          <span className="text-slate-500">Entregado</span>
          <span className="font-semibold text-slate-700 nums">{avance}%</span>
        </div>
        <div className="h-2 overflow-hidden rounded-full bg-slate-100">
          <div
            className="h-full rounded-full bg-success transition-all"
            style={{ width: `${avance}%` }}
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <Mini tono="success" valor={c.entregados} etiqueta="Entregados" />
        <Mini tono="info" valor={c.en_proceso} etiqueta="En proceso" />
        <Mini tono="warning" valor={c.pendientes} etiqueta="Pendientes" />
        <Mini tono="danger" valor={c.fallidos} etiqueta="Fallidos" />
      </div>

      {/* CUS-36: liquidación del cliente (genera y descarga el Excel) */}
      <Button
        variant="secondary"
        size="sm"
        block
        className="mt-4"
        icon={generando ? Loader2 : FileSpreadsheet}
        onClick={descargar}
        disabled={generando}
      >
        {generando ? "Generando…" : "Descargar liquidación (Excel)"}
      </Button>
      {error && <p className="mt-2 text-xs text-danger-strong">{error}</p>}
    </Card>
  );
}
