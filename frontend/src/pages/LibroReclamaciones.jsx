import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { BookText, Search, X, AlertTriangle, Clock, CheckCircle2, Send, ExternalLink } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import KpiCard from "../components/ui/KpiCard";
import SectionCard from "../components/ui/SectionCard";
import DataTable from "../components/ui/DataTable";
import Input from "../components/ui/Input";
import Button from "../components/ui/Button";
import Badge from "../components/ui/Badge";
import Modal from "../components/ui/Modal";
import { listarReclamos, responderReclamo } from "../services/api";

// Fecha legible corta (es-PE). Entrada: fecha ISO. Salida: "dd/mm/aa hh:mm" o "—".
const fmt = (f) => (f ? new Date(f).toLocaleString("es-PE", { dateStyle: "short", timeStyle: "short" }) : "—");
// Día legible de una fecha AAAA-MM-DD (sin desfase de zona). Entrada: fecha ISO corta.
const dia = (f) => (f ? new Date(`${f}T12:00:00`).toLocaleDateString("es-PE", { day: "2-digit", month: "2-digit", year: "numeric" }) : "—");

const FILTROS = [
  { id: "PENDIENTES", label: "Pendientes" },
  { id: "RESPONDIDOS", label: "Respondidos" },
  { id: "TODOS", label: "Todos" },
];

// Etiqueta del plazo legal de 15 días hábiles (C41-03). Recibe el plazo que calcula el servidor.
function BadgePlazo({ plazo }) {
  if (!plazo) return null;
  if (plazo.estado === "RESPONDIDO") {
    return <Badge tono={plazo.aTiempo ? "success" : "warning"}>{plazo.aTiempo ? "Respondido a tiempo" : "Respondido fuera de plazo"}</Badge>;
  }
  if (plazo.estado === "VENCIDO") return <Badge tono="danger">Vencido hace {-plazo.diasRestantes} d. háb.</Badge>;
  const texto = plazo.diasRestantes === 0 ? "Vence hoy" : `${plazo.diasRestantes} d. háb. · vence ${dia(plazo.venceEl)}`;
  return <Badge tono={plazo.estado === "POR_VENCER" ? "warning" : "info"}>{texto}</Badge>;
}

// Libro de Reclamaciones del panel: detalle completo, respuesta al consumidor y control del plazo legal (C41-01..03).
export default function LibroReclamaciones() {
  const [params, setParams] = useSearchParams();
  const [reclamos, setReclamos] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [busqueda, setBusqueda] = useState("");
  const [filtro, setFiltro] = useState("PENDIENTES");
  const [seleccionado, setSeleccionado] = useState(null);

  // Vuelve a pedir los reclamos. Sin parámetros.
  const cargar = () =>
    listarReclamos()
      .then((d) => setReclamos(Array.isArray(d) ? d : []))
      .catch(() => {})
      .finally(() => setCargando(false));

  useEffect(() => {
    let activo = true;
    listarReclamos()
      .then((d) => activo && setReclamos(Array.isArray(d) ? d : []))
      .catch(() => {})
      .finally(() => activo && setCargando(false));
    return () => { activo = false; };
  }, []);

  // Reclamo a abrir desde la URL (?codigo=LR-2026-0001), p. ej. desde la campana.
  const codigoUrl = (params.get("codigo") || "").toUpperCase();
  const deUrl = useMemo(() => (codigoUrl ? reclamos.find((r) => (r.codigo || "").toUpperCase() === codigoUrl) || null : null), [codigoUrl, reclamos]);
  const abierto = seleccionado ? reclamos.find((r) => r.id === seleccionado.id) || seleccionado : deUrl;

  // Cierra el detalle y limpia el código de la URL. Sin parámetros.
  const cerrar = () => {
    setSeleccionado(null);
    if (codigoUrl) {
      const siguientes = new URLSearchParams(params);
      siguientes.delete("codigo");
      setParams(siguientes, { replace: true });
    }
  };

  const kpis = useMemo(() => {
    const pendientes = reclamos.filter((r) => r.plazo?.estado !== "RESPONDIDO");
    return {
      total: reclamos.length,
      pendientes: pendientes.length,
      porVencer: pendientes.filter((r) => r.plazo?.estado === "POR_VENCER").length,
      vencidos: pendientes.filter((r) => r.plazo?.estado === "VENCIDO").length,
    };
  }, [reclamos]);

  const filtrados = useMemo(() => {
    const q = busqueda.trim().toLowerCase();
    return reclamos.filter((r) => {
      const respondido = r.plazo?.estado === "RESPONDIDO";
      if (filtro === "PENDIENTES" && respondido) return false;
      if (filtro === "RESPONDIDOS" && !respondido) return false;
      if (!q) return true;
      return [r.codigo, r.consumidor, r.pedido, r.dni].some((v) => (v || "").toLowerCase().includes(q));
    });
  }, [reclamos, busqueda, filtro]);

  const columnas = [
    { key: "codigo", header: "Código", render: (r) => <span className="font-medium text-slate-800 nums">{r.codigo || "—"}</span> },
    { key: "tipo", header: "Tipo", render: (r) => <span className="text-slate-700">{r.tipo === "QUEJA" ? "Queja" : "Reclamo"}</span> },
    { key: "consumidor", header: "Consumidor", render: (r) => (
      <div>
        <p className="font-medium text-slate-700">{r.consumidor || "—"}</p>
        <p className="text-xs text-slate-500">{r.dni ? `Doc. ${r.dni}` : r.email || ""}</p>
      </div>
    ) },
    { key: "pedido", header: "Pedido", render: (r) => <span className="text-slate-600 nums">{r.pedido || "—"}</span> },
    { key: "plazo", header: "Plazo legal", render: (r) => <BadgePlazo plazo={r.plazo} /> },
    { key: "creado_en", header: "Registrado", render: (r) => <span className="text-xs text-slate-500 nums">{fmt(r.creado_en)}</span> },
  ];

  return (
    <div className="space-y-6 p-6 lg:p-8 animate-fade-in">
      <PageHeader titulo="Libro de Reclamaciones" subtitulo="Reclamos y quejas del sitio público. La ley da 15 días hábiles para responder." />

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4 animate-fade-up">
        <KpiCard label="Total" value={kpis.total} icon={BookText} tone="brand" />
        <KpiCard label="Pendientes" value={kpis.pendientes} icon={Clock} tone="info" />
        <KpiCard label="Por vencer (≤3 d.)" value={kpis.porVencer} icon={AlertTriangle} tone="warning" />
        <KpiCard label="Vencidos" value={kpis.vencidos} icon={AlertTriangle} tone="danger" />
      </div>

      {(kpis.vencidos > 0 || kpis.porVencer > 0) && (
        <div role="alert" className="flex items-start gap-3 rounded-xl border border-danger/30 bg-danger-soft px-4 py-3 text-sm text-danger-strong animate-fade-up">
          <AlertTriangle size={18} className="mt-0.5 shrink-0" />
          <p>
            {kpis.vencidos > 0 && <><b>{kpis.vencidos}</b> {kpis.vencidos === 1 ? "reclamo venció" : "reclamos vencieron"} sin respuesta. </>}
            {kpis.porVencer > 0 && <><b>{kpis.porVencer}</b> {kpis.porVencer === 1 ? "vence" : "vencen"} en 3 días hábiles o menos. </>}
            Responder fuera de plazo puede acarrear una sanción de INDECOPI.
          </p>
        </div>
      )}

      <SectionCard className="animate-fade-up" title="Reclamos" subtitle={`${filtrados.length} de ${reclamos.length}`}
        action={
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
            <Input as="select" value={filtro} onChange={(e) => setFiltro(e.target.value)} aria-label="Filtrar reclamos">
              {FILTROS.map((f) => <option key={f.id} value={f.id}>{f.label}</option>)}
            </Input>
            <div className="relative">
              <Search size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <Input value={busqueda} onChange={(e) => setBusqueda(e.target.value)} placeholder="Código, consumidor o pedido" className="pl-9" />
            </div>
          </div>
        }
      >
        <DataTable columns={columnas} rows={filtrados} rowKey={(r) => r.id} loading={cargando}
          onRowClick={(r) => setSeleccionado(r)}
          empty={{ icon: BookText, title: "Sin reclamos", description: "No hay reclamos que coincidan con el filtro." }} />
      </SectionCard>

      <Modal open={!!abierto} onClose={cerrar} variant="right">
        {abierto && <DetalleReclamo key={abierto.id} reclamo={abierto} onCerrar={cerrar} onRespondido={cargar} />}
      </Modal>
    </div>
  );
}

// Detalle completo del reclamo con enlace al pedido y la respuesta al consumidor (C41-01, C41-02).
// Recibe reclamo, onCerrar y onRespondido.
function DetalleReclamo({ reclamo: r, onCerrar, onRespondido }) {
  const [respuesta, setRespuesta] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [aviso, setAviso] = useState(null);

  // Guarda la respuesta al consumidor. Sin parámetros.
  const responder = () => {
    setEnviando(true);
    setAviso(null);
    responderReclamo(r.id, respuesta.trim())
      .then((res) => {
        setAviso({ ok: true, texto: res.correoEnviado ? "Respuesta registrada y enviada al correo del consumidor." : "Respuesta registrada. El correo está apagado: envíasela al consumidor por otro medio." });
        onRespondido();
      })
      .catch((e) => setAviso({ ok: false, texto: e.message }))
      .finally(() => setEnviando(false));
  };

  return (
    <>
      <div className="flex items-center justify-between border-b border-slate-100 px-6 py-4">
        <div>
          <h2 className="font-bold text-slate-900 nums">{r.codigo}</h2>
          <div className="mt-1 flex flex-wrap items-center gap-2">
            <Badge tono="neutral">{r.tipo === "QUEJA" ? "Queja" : "Reclamo"}</Badge>
            <BadgePlazo plazo={r.plazo} />
          </div>
        </div>
        <button onClick={onCerrar} aria-label="Cerrar" className="rounded-lg p-2 text-slate-500 hover:bg-slate-100"><X size={20} /></button>
      </div>

      <div className="space-y-5 px-6 py-5">
        <Bloque titulo="Consumidor">
          <Dato etiqueta="Nombre" valor={r.consumidor} />
          <Dato etiqueta="Documento" valor={r.dni} />
          <Dato etiqueta="Domicilio" valor={r.domicilio} />
          <Dato etiqueta="Teléfono" valor={r.telefono} />
          <Dato etiqueta="Correo" valor={r.email} />
          {r.esMenor && <Dato etiqueta="Menor de edad · padre o madre" valor={`${r.apoderadoNombre || "—"} · Doc. ${r.apoderadoDni || "—"}`} />}
        </Bloque>

        <Bloque titulo="Bien contratado">
          <Dato etiqueta={r.bienTipo === "PRODUCTO" ? "Producto" : "Servicio"} valor={r.bienDescripcion} />
          <Dato etiqueta="Monto reclamado" valor={r.monto != null ? `S/ ${Number(r.monto).toFixed(2)}` : "—"} />
          <div className="text-sm">
            <p className="text-slate-400">Pedido SAVA</p>
            {r.pedido ? (
              <Link to={`/panel/pedidos?codigo=${encodeURIComponent(r.pedido)}`} className="inline-flex items-center gap-1 font-medium text-brand-600 hover:underline">
                {r.pedido} <ExternalLink size={13} /> <span className="font-normal text-slate-500">ver trazabilidad</span>
              </Link>
            ) : <p className="font-medium text-slate-700">—</p>}
          </div>
        </Bloque>

        <Bloque titulo="Reclamación">
          <Dato etiqueta="Detalle" valor={r.detalle} />
          <Dato etiqueta="Pedido del consumidor" valor={r.pedidoConsumidor} />
          <Dato etiqueta="Registrado" valor={fmt(r.creado_en)} />
          <Dato etiqueta="Responder a más tardar" valor={dia(r.plazo?.venceEl)} />
        </Bloque>

        {r.respondidoEn ? (
          <div className="rounded-xl border border-success/30 bg-success-soft p-4">
            <p className="flex items-center gap-1.5 text-sm font-semibold text-success-strong">
              <CheckCircle2 size={16} /> Respondido · {fmt(r.respondidoEn)}
            </p>
            <p className="mt-1.5 whitespace-pre-line text-sm text-slate-700">{r.respuesta}</p>
          </div>
        ) : (
          <div className="space-y-3 rounded-xl border border-warning/40 bg-warning-soft p-4">
            <p className="text-sm font-semibold text-warning-strong">Respuesta al consumidor</p>
            <Input as="textarea" rows={5} maxLength={4000} value={respuesta} onChange={(e) => setRespuesta(e.target.value)}
              placeholder="Escribe la respuesta que recibirá el consumidor…" hint="Queda registrada con su fecha y no se puede editar después." />
            <Button icon={Send} block onClick={responder} disabled={enviando || respuesta.trim().length < 10}>
              {enviando ? "Guardando…" : "Registrar respuesta"}
            </Button>
          </div>
        )}

        {aviso && (
          <p className={`rounded-xl px-4 py-2.5 text-sm ${aviso.ok ? "bg-success-soft text-success-strong" : "bg-danger-soft text-danger-strong"}`}>{aviso.texto}</p>
        )}
      </div>
    </>
  );
}

// Grupo de datos con título. Recibe titulo y children.
function Bloque({ titulo, children }) {
  return (
    <div>
      <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">{titulo}</h3>
      <div className="space-y-2.5">{children}</div>
    </div>
  );
}

// Fila etiqueta + valor. Recibe etiqueta y valor.
function Dato({ etiqueta, valor }) {
  return (
    <div className="text-sm">
      <p className="text-slate-400">{etiqueta}</p>
      <p className="whitespace-pre-line font-medium text-slate-700">{valor || "—"}</p>
    </div>
  );
}
