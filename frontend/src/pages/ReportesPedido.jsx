import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { ClipboardList, Search, CheckCircle2, MessageSquare, X, AlertTriangle, RotateCcw, Ban } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import KpiCard from "../components/ui/KpiCard";
import SectionCard from "../components/ui/SectionCard";
import DataTable from "../components/ui/DataTable";
import Input from "../components/ui/Input";
import Button from "../components/ui/Button";
import Badge from "../components/ui/Badge";
import Modal from "../components/ui/Modal";
import ConfirmDialog from "../components/ui/ConfirmDialog";
import SolicitudesReprogramacion from "../components/SolicitudesReprogramacion";
import { etiquetaEstado } from "../utils/estados";
import { listarReportes, responderReporte } from "../services/api";

// Fecha legible corta (es-PE). Entrada: fecha ISO. Salida: "dd/mm/aa hh:mm" o "—".
const fmt = (f) => (f ? new Date(f).toLocaleString("es-PE", { dateStyle: "short", timeStyle: "short" }) : "—");

// Decisiones posibles sobre el pedido al responder el reporte (C31-01).
const DECISIONES = [
  { id: "REPROGRAMAR", titulo: "Reprogramar", detalle: "Vuelve a Listo para envío", icono: RotateCcw, boton: "Responder y reprogramar" },
  { id: "CANCELAR", titulo: "Cancelar pedido", detalle: "Definitivo, con motivo", icono: Ban, boton: "Responder y cancelar" },
  { id: "NINGUNA", titulo: "Solo responder", detalle: "El pedido no cambia", icono: MessageSquare, boton: "Marcar resuelto" },
];

// Badge de estado del reporte. Recibe: estado ("ABIERTO" | "RESUELTO").
function BadgeEstado({ estado }) {
  if (estado === "RESUELTO") return <Badge tono="success">Resuelto</Badge>;
  return <Badge tono="warning">Abierto</Badge>;
}

// Tabla de reportes de conductores con filtros de estado/busqueda y panel de resolucion.
export default function ReportesPedido() {
  const [params] = useSearchParams();
  const [reportes, setReportes] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [estado, setEstado] = useState(() =>
    params.get("pendientes") === "1" || params.get("estado") === "ABIERTO" ? "ABIERTO" : "TODOS"
  ); // TODOS | ABIERTO | RESUELTO
  const [busqueda, setBusqueda] = useState(() => params.get("pedido") || "");
  const [seleccionado, setSeleccionado] = useState(null);

  useEffect(() => {
    let activo = true;
    listarReportes()
      .then((d) => activo && setReportes(Array.isArray(d) ? d : []))
      .catch(() => {})
      .finally(() => activo && setCargando(false));
    return () => { activo = false; };
  }, []);

  // Recarga la lista de reportes (tras responder uno) sin tocar el spinner inicial.
  const recargar = () => {
    listarReportes()
      .then((d) => setReportes(Array.isArray(d) ? d : []))
      .catch(() => {});
  };

  // KPIs derivados de la lista cargada (sin fetch extra).
  const kpis = useMemo(() => ({
    total: reportes.length,
    abiertos: reportes.filter((r) => r.estado === "ABIERTO").length,
    resueltos: reportes.filter((r) => r.estado === "RESUELTO").length,
  }), [reportes]);

  // Aplica los filtros de estado y búsqueda sobre la lista (client-side).
  const filtrados = useMemo(() => {
    const q = busqueda.trim().toLowerCase();
    return reportes.filter((r) => {
      if (estado !== "TODOS" && r.estado !== estado) return false;
      if (!q) return true;
      return (
        (r.pedido_codigo || "").toLowerCase().includes(q) ||
        (r.conductor_nombre || "").toLowerCase().includes(q)
      );
    });
  }, [reportes, estado, busqueda]);

  const columnas = [
    { key: "pedido_codigo", header: "Pedido", render: (r) => (
      <div>
        <p className="font-medium text-slate-800 nums">{r.pedido_codigo || "—"}</p>
        <p className="text-xs text-slate-500 line-clamp-1">{r.direccion_destino || ""}</p>
      </div>
    ) },
    { key: "conductor_nombre", header: "Conductor", render: (r) => <span className="text-slate-700">{r.conductor_nombre || "—"}</span> },
    { key: "motivo", header: "Motivo", render: (r) => (
      <div>
        <p className="font-medium text-slate-700">{r.motivo || "—"}</p>
        {r.descripcion && <p className="text-xs text-slate-500 line-clamp-2">{r.descripcion}</p>}
      </div>
    ) },
    { key: "estado", header: "Estado", render: (r) => <BadgeEstado estado={r.estado} /> },
    { key: "respuesta", header: "Respuesta del admin", render: (r) => (
      r.respuesta
        ? <div className="flex items-start gap-1.5 text-slate-600"><MessageSquare size={14} className="mt-0.5 shrink-0 text-slate-400" /><span className="line-clamp-2 text-xs">{r.respuesta}</span></div>
        : <span className="text-xs text-slate-400">Sin respuesta</span>
    ) },
    { key: "creado_en", header: "Fecha", render: (r) => (
      <div className="text-xs text-slate-500 nums">
        <p>{fmt(r.creado_en)}</p>
        {r.respondido_en && <p className="text-slate-400">Resp. {fmt(r.respondido_en)}</p>}
      </div>
    ) },
  ];

  return (
    <div className="space-y-6 p-6 lg:p-8 animate-fade-in">
      <PageHeader titulo="Reportes de pedido" subtitulo="Reportes que los conductores levantan sobre los pedidos. Ábrelos para responder y marcarlos resueltos." />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3 animate-fade-up">
        <KpiCard label="Total" value={kpis.total} icon={ClipboardList} tone="brand" />
        <KpiCard label="Abiertos" value={kpis.abiertos} icon={ClipboardList} tone="warning" />
        <KpiCard label="Resueltos" value={kpis.resueltos} icon={CheckCircle2} tone="success" />
      </div>

      <SectionCard className="animate-fade-up" title="Reportes" subtitle={`${filtrados.length} de ${reportes.length}`}
        action={
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
            <div className="relative">
              <Search size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <Input value={busqueda} onChange={(e) => setBusqueda(e.target.value)} placeholder="Código de pedido o conductor" className="pl-9" />
            </div>
            <Input as="select" value={estado} onChange={(e) => setEstado(e.target.value)}>
              <option value="TODOS">Todos los estados</option>
              <option value="ABIERTO">Abiertos</option>
              <option value="RESUELTO">Resueltos</option>
            </Input>
          </div>
        }
      >
        <DataTable columns={columnas} rows={filtrados} rowKey={(r) => r.id} loading={cargando}
          onRowClick={(r) => setSeleccionado(r)}
          empty={{ icon: ClipboardList, title: "Sin reportes", description: "No hay reportes que coincidan con el filtro." }} />
      </SectionCard>

      <Modal open={!!seleccionado} onClose={() => setSeleccionado(null)} variant="right">
        {seleccionado && (
          <DetalleReporte
            reporte={seleccionado}
            onCerrar={() => setSeleccionado(null)}
            onResuelto={() => { setSeleccionado(null); recargar(); }}
          />
        )}
      </Modal>
    </div>
  );
}

// Panel lateral de detalle y resolucion de un reporte. Recibe: reporte, onCerrar, onResuelto.
function DetalleReporte({ reporte: r, onCerrar, onResuelto }) {
  const decidible = r.pedido_estado === "FALLIDO";
  const [respuesta, setRespuesta] = useState("");
  const [accion, setAccion] = useState(decidible ? "REPROGRAMAR" : "NINGUNA");
  const [motivoCancelacion, setMotivoCancelacion] = useState("");
  const [confirmar, setConfirmar] = useState(false);
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState("");
  const decision = DECISIONES.find((d) => d.id === accion) || DECISIONES[2];
  const listo = respuesta.trim() && (accion !== "CANCELAR" || motivoCancelacion.trim().length >= 5);

  // Responde el reporte y aplica la decisión sobre el pedido en el mismo paso (C31-01). Sin parámetros.
  const enviar = () => {
    if (!listo) return;
    setGuardando(true);
    setError("");
    responderReporte(r.id, {
      respuesta: respuesta.trim(),
      accion,
      motivo_cancelacion: accion === "CANCELAR" ? motivoCancelacion.trim() : undefined,
    })
      .then(() => onResuelto())
      .catch((e) => { setError(e.message); setGuardando(false); setConfirmar(false); });
  };

  return (
    <>
      <div className="flex items-center justify-between border-b border-slate-100 px-6 py-4">
        <div className="flex items-center gap-2">
          <AlertTriangle size={20} className="text-warning-strong shrink-0" />
          <div>
            <h2 className="font-bold text-slate-900 nums">{r.pedido_codigo || "Reporte"}</h2>
            <BadgeEstado estado={r.estado} />
          </div>
        </div>
        <button onClick={onCerrar} aria-label="Cerrar" className="rounded-lg p-2 text-slate-500 hover:bg-slate-100"><X size={20} /></button>
      </div>

      <div className="space-y-4 px-6 py-5">
        <Dato etiqueta="Pedido" valor={r.pedido_codigo || "—"} />
        {r.direccion_destino && <Dato etiqueta="Dirección" valor={r.direccion_destino} />}
        <Dato etiqueta="Conductor" valor={r.conductor_nombre || "—"} />
        <Dato etiqueta="Motivo" valor={r.motivo || "—"} />
        {r.descripcion && <Dato etiqueta="Descripción" valor={r.descripcion} />}
        <Dato etiqueta="Reportado" valor={fmt(r.creado_en)} />
        {r.url_evidencia && (
          <div>
            <p className="mb-1.5 text-xs text-slate-400">Foto del conductor</p>
            <a href={r.url_evidencia} target="_blank" rel="noreferrer">
              <img src={r.url_evidencia} alt="Foto que respalda la entrega fallida" className="max-h-56 w-full rounded-xl object-cover" />
            </a>
            {r.latitud_longitud_captura && (
              <a href={`https://www.google.com/maps?q=${r.latitud_longitud_captura}`} target="_blank" rel="noreferrer"
                className="mt-1.5 inline-block text-xs font-medium text-brand-600 hover:underline">
                Ver dónde se tomó la foto
              </a>
            )}
          </div>
        )}

        <SolicitudesReprogramacion pedidoId={r.pedido_id} pedidoEstado={r.pedido_estado} />

        {error && (
          <p className="rounded-xl bg-danger-soft px-4 py-2.5 text-sm text-danger-strong">{error}</p>
        )}

        {r.estado === "ABIERTO" && (
          <div className="space-y-3 rounded-xl border border-warning/40 bg-warning-soft p-4">
            <p className="text-sm font-semibold text-warning-strong">Responder y decidir</p>
            {decidible ? (
              <div role="radiogroup" aria-label="Decisión sobre el pedido" className="grid grid-cols-3 gap-2">
                {DECISIONES.map((d) => {
                  const activa = accion === d.id;
                  const Icono = d.icono;
                  return (
                    <button
                      key={d.id}
                      type="button"
                      role="radio"
                      aria-checked={activa}
                      onClick={() => setAccion(d.id)}
                      className={`rounded-xl border px-2.5 py-2 text-left transition ${activa
                        ? (d.id === "CANCELAR" ? "border-danger bg-white ring-2 ring-danger/20" : "border-brand-500 bg-white ring-2 ring-brand-500/20")
                        : "border-slate-200 bg-white/60 hover:bg-white"}`}
                    >
                      <span className={`flex items-center gap-1.5 text-xs font-semibold ${activa && d.id === "CANCELAR" ? "text-danger-strong" : "text-slate-800"}`}>
                        <Icono size={14} className="shrink-0" /> {d.titulo}
                      </span>
                      <span className="mt-0.5 block text-[11px] leading-tight text-slate-500">{d.detalle}</span>
                    </button>
                  );
                })}
              </div>
            ) : (
              <p className="text-xs text-slate-600">
                El pedido está {etiquetaEstado(r.pedido_estado || "").toLowerCase() || "sin estado"}: solo puedes responder al conductor.
              </p>
            )}
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-500">Respuesta <span className="text-danger">*</span></label>
              <textarea
                value={respuesta}
                onChange={(e) => setRespuesta(e.target.value)}
                placeholder="Escribe la respuesta o instrucción para el conductor…"
                rows={3}
                className="w-full rounded-xl border border-slate-200 bg-white p-3 text-sm text-slate-800 placeholder:text-slate-400 outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/30 resize-none"
              />
            </div>
            {accion === "CANCELAR" && (
              <Input
                as="textarea"
                label="Motivo de la cancelación"
                rows={2}
                maxLength={255}
                value={motivoCancelacion}
                onChange={(e) => setMotivoCancelacion(e.target.value)}
                placeholder="Ej. Dirección inexistente confirmada con la tienda"
                hint="Obligatorio (mínimo 5 caracteres). Queda en el historial del pedido."
              />
            )}
            <Button
              icon={decision.icono === MessageSquare ? CheckCircle2 : decision.icono}
              variant={accion === "CANCELAR" ? "danger" : "primary"}
              block
              onClick={() => (accion === "CANCELAR" ? setConfirmar(true) : enviar())}
              disabled={guardando || !listo}
            >
              {guardando ? "Guardando…" : decision.boton}
            </Button>
          </div>
        )}

        <ConfirmDialog
          open={confirmar}
          titulo={`¿Cancelar el pedido ${r.pedido_codigo || ""}?`}
          mensaje="El pedido queda cancelado de forma definitiva y el reporte se marca resuelto con tu respuesta."
          textoConfirmar="Sí, cancelar pedido"
          tono="danger"
          cargando={guardando}
          onConfirmar={enviar}
          onCancelar={() => setConfirmar(false)}
        />

        {r.estado === "RESUELTO" && (
          <div className="space-y-2 rounded-xl border border-success/30 bg-success-soft p-4">
            <p className="flex items-center gap-1.5 text-sm font-semibold text-success-strong">
              <CheckCircle2 size={16} /> Resuelto {r.respondido_en ? `· ${fmt(r.respondido_en)}` : ""}
            </p>
            <p className="text-sm text-slate-700">{r.respuesta || "Sin respuesta registrada."}</p>
            {r.accion && <p className="text-xs text-slate-500"><span className="font-medium">Acción:</span> {r.accion}</p>}
          </div>
        )}
      </div>
    </>
  );
}

// Fila de dato simple con etiqueta + valor (para el panel de detalle).
function Dato({ etiqueta, valor }) {
  return (
    <div className="text-sm">
      <p className="text-slate-400">{etiqueta}</p>
      <p className="font-medium text-slate-700">{valor}</p>
    </div>
  );
}
