import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Wrench, CheckCircle2, X, MapPin, Send, ShieldCheck } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import KpiCard from "../components/ui/KpiCard";
import SectionCard from "../components/ui/SectionCard";
import DataTable from "../components/ui/DataTable";
import Input from "../components/ui/Input";
import Button from "../components/ui/Button";
import Badge from "../components/ui/Badge";
import Modal from "../components/ui/Modal";
import { listarIncidencias, mandarAyuda } from "../services/api";

// Fecha legible corta (es-PE). Entrada: fecha ISO. Salida: "dd/mm/aa hh:mm" o "—".
const fmt = (f) => (f ? new Date(f).toLocaleString("es-PE", { dateStyle: "short", timeStyle: "short" }) : "—");

const TIPOS_AYUDA = ["Mecánico", "Grúa", "Combustible", "Vehículo de reemplazo", "Otro"];

// Badge del estado de la incidencia. Recibe estado (ABIERTA/RESUELTA).
function BadgeEstado({ estado }) {
  if (estado === "RESUELTA") return <Badge tono="success">Resuelta</Badge>;
  return <Badge tono="danger">Abierta</Badge>;
}

// Tabla de incidencias mecánicas de la flota con filtros y panel de envío de ayuda.
export default function AuxilioMecanico() {
  const [params] = useSearchParams();
  const [incidencias, setIncidencias] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [conductorId, setConductorId] = useState(() => params.get("conductor") || "TODOS");
  const [estado, setEstado] = useState(() => (params.get("estado") === "ABIERTA" ? "ABIERTA" : "TODAS"));
  const [seleccionada, setSeleccionada] = useState(null);

  useEffect(() => {
    let activo = true;
    listarIncidencias()
      .then((d) => activo && setIncidencias(Array.isArray(d) ? d : []))
      .catch(() => {})
      .finally(() => activo && setCargando(false));
    return () => { activo = false; };
  }, []);

  // Recarga incidencias sin mostrar spinner. Sin parámetros.
  const recargar = () => {
    listarIncidencias()
      .then((d) => setIncidencias(Array.isArray(d) ? d : []))
      .catch(() => {});
  };

  // Lista de conductores únicos para el filtro dropdown.
  const conductores = useMemo(() => {
    const mapa = new Map();
    incidencias.forEach((i) => {
      if (i.conductor_id != null && !mapa.has(i.conductor_id)) {
        mapa.set(i.conductor_id, i.conductor_nombre || `Conductor ${i.conductor_id}`);
      }
    });
    return [...mapa.entries()].map(([id, nombre]) => ({ id, nombre }));
  }, [incidencias]);

  // KPIs calculados desde la lista cargada.
  const kpis = useMemo(() => ({
    total: incidencias.length,
    abiertas: incidencias.filter((i) => i.estado === "ABIERTA").length,
    resueltas: incidencias.filter((i) => i.estado === "RESUELTA").length,
  }), [incidencias]);

  // Filtra incidencias por conductor y estado (client-side).
  const filtradas = useMemo(() => {
    return incidencias.filter((i) => {
      if (estado !== "TODAS" && i.estado !== estado) return false;
      if (conductorId !== "TODOS" && String(i.conductor_id) !== String(conductorId)) return false;
      return true;
    });
  }, [incidencias, conductorId, estado]);

  const columnas = [
    { key: "codigo", header: "Código", render: (i) => <span className="font-medium text-slate-800 nums">{i.codigo || "—"}</span> },
    { key: "conductor_nombre", header: "Conductor", render: (i) => (
      <div>
        <p className="font-medium text-slate-700">{i.conductor_nombre || "—"}</p>
        <p className="text-xs text-slate-500">{i.vehiculo_placa || "Sin vehículo"}</p>
      </div>
    ) },
    { key: "ruta_nombre", header: "Ruta", render: (i) => <span className="text-slate-600">{i.ruta_nombre || "—"}</span> },
    { key: "tipo", header: "Incidencia", render: (i) => (
      <div>
        <p className="font-medium text-slate-700">{i.tipo || "—"}</p>
        {i.descripcion && <p className="text-xs text-slate-500 line-clamp-2">{i.descripcion}</p>}
      </div>
    ) },
    { key: "puede_solucionar_solo", header: "Puede solo", render: (i) => (
      i.puede_solucionar_solo
        ? <Badge tono="info">Sí</Badge>
        : <span className="text-xs text-slate-400">—</span>
    ) },
    { key: "ayuda", header: "Ayuda", render: (i) => (
      i.ayuda_enviada_en
        ? (
          <div className="text-xs text-slate-600">
            <p className="font-medium">{i.ayuda_detalle || "Enviada"}</p>
            <p className="text-slate-400 nums">{fmt(i.ayuda_enviada_en)}</p>
          </div>
        )
        : <span className="text-xs text-slate-400">—</span>
    ) },
    { key: "estado", header: "Estado", render: (i) => <BadgeEstado estado={i.estado} /> },
    { key: "creado_en", header: "Fecha", render: (i) => (
      <div className="text-xs text-slate-500 nums">
        <p>{fmt(i.creado_en)}</p>
        {i.resuelto_en && <p className="text-slate-400">Res. {fmt(i.resuelto_en)}</p>}
      </div>
    ) },
  ];

  return (
    <div className="space-y-6 p-6 lg:p-8 animate-fade-in">
      <PageHeader titulo="Auxilio mecánico" subtitulo="Incidencias mecánicas reportadas por los conductores en ruta. Ábrelas para mandar ayuda." />

      <div className="grid grid-cols-3 gap-4 animate-fade-up">
        <KpiCard label="Total" value={kpis.total} icon={Wrench} tone="brand" />
        <KpiCard label="Abiertas" value={kpis.abiertas} icon={Wrench} tone="danger" />
        <KpiCard label="Resueltas" value={kpis.resueltas} icon={CheckCircle2} tone="success" />
      </div>

      <SectionCard className="animate-fade-up" title="Incidencias" subtitle={`${filtradas.length} de ${incidencias.length}`}
        action={
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
            <Input as="select" value={conductorId} onChange={(e) => setConductorId(e.target.value)}>
              <option value="TODOS">Todos los conductores</option>
              {conductores.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
            </Input>
            <Input as="select" value={estado} onChange={(e) => setEstado(e.target.value)}>
              <option value="TODAS">Todos los estados</option>
              <option value="ABIERTA">Abiertas</option>
              <option value="RESUELTA">Resueltas</option>
            </Input>
          </div>
        }
      >
        <DataTable columns={columnas} rows={filtradas} rowKey={(i) => i.id} loading={cargando}
          onRowClick={(i) => setSeleccionada(i)}
          empty={{ icon: Wrench, title: "Sin incidencias", description: "No hay incidencias que coincidan con el filtro." }} />
      </SectionCard>

      <Modal open={!!seleccionada} onClose={() => setSeleccionada(null)} variant="right">
        {seleccionada && (
          <DetalleIncidencia
            incidencia={seleccionada}
            onCerrar={() => setSeleccionada(null)}
            onAyudaEnviada={() => { setSeleccionada(null); recargar(); }}
          />
        )}
      </Modal>
    </div>
  );
}

// Detalle de una incidencia con formulario de envío de ayuda. Recibe incidencia, onCerrar, onAyudaEnviada.
function DetalleIncidencia({ incidencia: i, onCerrar, onAyudaEnviada }) {
  const [mostrarForm, setMostrarForm] = useState(!i.ayuda_enviada_en);
  const [tipo, setTipo] = useState(TIPOS_AYUDA[0]);
  const [nota, setNota] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState("");

  const puedeSolo = i.puede_solucionar_solo;
  const yaEnviada = !!i.ayuda_enviada_en;

  // Envía o reenvía la ayuda al backend. Recibe tipo y nota del estado local.
  const enviarAyuda = () => {
    if (!tipo) return;
    setEnviando(true);
    setError("");
    mandarAyuda(i.id, { tipo, nota: nota.trim() || undefined })
      .then(() => onAyudaEnviada())
      .catch((e) => { setError(e.message); setEnviando(false); });
  };

  return (
    <>
      <div className="flex items-center justify-between border-b border-slate-100 px-6 py-4">
        <div className="flex items-center gap-2">
          <Wrench size={20} className="text-danger shrink-0" />
          <div>
            <h2 className="font-bold text-slate-900 nums">{i.codigo ?? `IN-${i.id}`}</h2>
            <BadgeEstado estado={i.estado} />
          </div>
        </div>
        <button onClick={onCerrar} aria-label="Cerrar" className="rounded-lg p-2 text-slate-500 hover:bg-slate-100"><X size={20} /></button>
      </div>

      <div className="space-y-4 px-6 py-5">
        {i.vehiculo_placa && <Dato etiqueta="Placa" valor={i.vehiculo_placa} />}
        <Dato etiqueta="Ruta" valor={i.ruta_nombre ?? (i.ruta_id ? `Ruta ${i.ruta_id}` : "—")} />
        <Dato etiqueta="Conductor" valor={i.conductor_nombre ?? "—"} />
        {i.tipo && <Dato etiqueta="Incidencia" valor={i.tipo} />}
        <Dato etiqueta="Descripción" valor={i.descripcion || "Sin detalle"} />
        <Dato etiqueta="Reportada" valor={fmt(i.creado_en)} />

        {i.latitud != null && i.longitud != null && (
          <a
            className="inline-flex items-center gap-1.5 rounded-xl bg-brand-50 px-4 py-2.5 text-sm font-medium text-brand-600 hover:underline"
            href={`https://www.google.com/maps?q=${i.latitud},${i.longitud}`}
            target="_blank"
            rel="noreferrer"
          >
            <MapPin size={15} /> Ver ubicación en Google Maps
          </a>
        )}

        {i.url_evidencia && (
          <div>
            <p className="mb-1.5 text-xs text-slate-400">Foto de evidencia</p>
            <img src={i.url_evidencia} alt="Evidencia de la avería" className="max-h-48 w-full rounded-xl object-cover" />
          </div>
        )}

        {error && (
          <p className="rounded-xl bg-danger-soft px-4 py-2.5 text-sm text-danger-strong">{error}</p>
        )}

        {i.estado === "ABIERTA" && (
          <>
            {puedeSolo && (
              <div className="flex items-start gap-2 rounded-xl border border-info/30 bg-info-soft p-4 text-sm text-info-strong">
                <ShieldCheck size={18} className="mt-0.5 shrink-0" />
                <span>El conductor indicó que puede resolverlo solo.</span>
              </div>
            )}

            {!puedeSolo && (
              <>
                {yaEnviada && (
                  <div className="rounded-xl border border-success/30 bg-success-soft p-4">
                    <p className="flex items-center gap-1.5 text-sm font-semibold text-success-strong">
                      <CheckCircle2 size={16} /> Ayuda enviada — {i.ayuda_detalle || "—"}
                    </p>
                    <p className="mt-0.5 text-xs text-slate-500 nums">{fmt(i.ayuda_enviada_en)}</p>
                    {!mostrarForm && (
                      <Button size="sm" variant="secondary" className="mt-3" onClick={() => setMostrarForm(true)}>
                        Reenviar / editar ayuda
                      </Button>
                    )}
                  </div>
                )}

                {mostrarForm && (
                  <div className="space-y-3 rounded-xl border border-warning/40 bg-warning-soft p-4">
                    <p className="text-sm font-semibold text-warning-strong">{yaEnviada ? "Editar ayuda" : "Mandar ayuda"}</p>
                    <Input as="select" label="Tipo de ayuda" value={tipo} onChange={(e) => setTipo(e.target.value)}>
                      {TIPOS_AYUDA.map((t) => <option key={t} value={t}>{t}</option>)}
                    </Input>
                    <div>
                      <label className="mb-1 block text-xs font-medium text-slate-500">Nota (opcional)</label>
                      <textarea
                        value={nota}
                        onChange={(e) => setNota(e.target.value)}
                        placeholder="Detalle de la ayuda enviada (ej. proveedor, hora estimada)…"
                        rows={3}
                        className="w-full rounded-xl border border-slate-200 bg-white p-3 text-sm text-slate-800 placeholder:text-slate-400 outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/30 resize-none"
                      />
                    </div>
                    <Button icon={Send} block onClick={enviarAyuda} disabled={enviando}>
                      {enviando ? "Enviando…" : yaEnviada ? "Reenviar ayuda" : "Mandar ayuda"}
                    </Button>
                  </div>
                )}
              </>
            )}
          </>
        )}

        {i.estado === "RESUELTA" && (
          <div className="rounded-xl border border-success/30 bg-success-soft p-4">
            <p className="flex items-center gap-1.5 text-sm font-semibold text-success-strong">
              <CheckCircle2 size={16} /> Resuelta {i.resuelto_en ? `· ${fmt(i.resuelto_en)}` : ""}
            </p>
            {i.nota_resolucion && <p className="mt-1 text-sm text-slate-700">{i.nota_resolucion}</p>}
          </div>
        )}
      </div>
    </>
  );
}

// Fila de etiqueta + valor para el panel de detalle. Recibe etiqueta y valor.
function Dato({ etiqueta, valor }) {
  return (
    <div className="text-sm">
      <p className="text-slate-400">{etiqueta}</p>
      <p className="font-medium text-slate-700">{valor}</p>
    </div>
  );
}
