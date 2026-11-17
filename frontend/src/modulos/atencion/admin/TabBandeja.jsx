// Pestaña "Bandeja": conversaciones que el visitante pidió pasar a una persona (o que el asistente
// no pudo resolver). Se ve la conversación (con DNI, teléfonos y correos ya ocultos) y se marca atendida.
import { useEffect, useState } from "react";
import { CheckCircle2, Inbox } from "lucide-react";
import SectionCard from "../../../components/ui/SectionCard";
import DataTable from "../../../components/ui/DataTable";
import Input from "../../../components/ui/Input";
import Button from "../../../components/ui/Button";
import Badge from "../../../components/ui/Badge";
import Modal from "../../../components/ui/Modal";
import { atenderDerivacion, detalleDerivacion, listarDerivaciones } from "./servicioAdminAtencion";

// Fecha legible corta. Recibe una fecha ISO (UTC sin zona).
const fmt = (f) => (f ? new Date(`${f}Z`).toLocaleString("es-PE", { dateStyle: "short", timeStyle: "short" }) : "—");
const ORIGEN = { visitante: "Lo pidió el visitante", asistente: "Lo derivó el asistente" };

// Detalle de una derivación con su conversación. Recibe el id y callbacks.
function DetalleDerivacion({ id, onCerrar, onAtendida }) {
  const [detalle, setDetalle] = useState(null);
  const [error, setError] = useState("");
  const [guardando, setGuardando] = useState(false);

  useEffect(() => {
    let vivo = true;
    detalleDerivacion(id).then((d) => vivo && setDetalle(d)).catch((e) => vivo && setError(e.message));
    return () => { vivo = false; };
  }, [id]);

  // Marca la derivación como atendida. Sin parámetros.
  const atender = async () => {
    setGuardando(true);
    try {
      setDetalle({ ...detalle, ...(await atenderDerivacion(id)) });
      onAtendida();
    } catch (e) {
      setError(e.message);
    } finally {
      setGuardando(false);
    }
  };

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-slate-200 px-6 py-4">
        <h2 className="text-lg font-semibold text-slate-900">Conversación derivada</h2>
        {detalle && <p className="text-xs text-slate-500">{ORIGEN[detalle.origen] || detalle.origen} · {fmt(detalle.creada_en)} · {detalle.pagina} · {detalle.idioma.toUpperCase()}</p>}
      </div>
      <div className="flex-1 space-y-4 overflow-y-auto px-6 py-4">
        {error && <p role="alert" className="text-sm text-danger-strong">{error}</p>}
        {!detalle && !error && <p className="text-sm text-slate-500">Cargando…</p>}
        {detalle && (
          <>
            <div className="rounded-xl bg-warm-50 px-4 py-3 text-sm">
              <p><span className="font-semibold text-slate-800">Motivo:</span> {detalle.motivo}</p>
              <p className="mt-1"><span className="font-semibold text-slate-800">Contacto:</span> {detalle.contacto || "No dejó un medio de contacto"}</p>
            </div>
            <ol className="space-y-2">
              {detalle.mensajes.map((m, i) => (
                <li key={i} className={`max-w-[90%] rounded-2xl px-3 py-2 text-sm ${m.rol === "usuario" ? "ml-auto bg-brand-600 text-white" : "bg-slate-100 text-slate-700"}`}>
                  <p className="whitespace-pre-wrap break-words">{m.contenido}</p>
                  <p className={`mt-1 text-[11px] ${m.rol === "usuario" ? "text-brand-100" : "text-slate-400"}`}>{fmt(m.creado_en)}{m.origen === "voz" ? " · voz" : ""}</p>
                </li>
              ))}
            </ol>
            <p className="text-xs text-slate-400">Los DNI, teléfonos y correos escritos en el chat se guardan ocultos. La conversación se borra sola al vencer la retención.</p>
          </>
        )}
      </div>
      <div className="flex justify-end gap-2 border-t border-slate-200 px-6 py-4">
        <Button variant="secondary" onClick={onCerrar}>Cerrar</Button>
        {detalle?.estado === "PENDIENTE" && <Button icon={CheckCircle2} disabled={guardando} onClick={atender}>Marcar como atendida</Button>}
      </div>
    </div>
  );
}

// Pestaña de la bandeja de derivaciones. Sin props.
export default function TabBandeja() {
  const [filas, setFilas] = useState([]);
  const [estado, setEstado] = useState("PENDIENTE");
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");
  const [abierta, setAbierta] = useState(null);
  const [recarga, setRecarga] = useState(0);

  // Trae las derivaciones del estado elegido (y cada vez que se pide recargar).
  useEffect(() => {
    let vivo = true;
    listarDerivaciones(estado === "TODAS" ? null : estado)
      .then((d) => { if (vivo) { setFilas(d); setError(""); } })
      .catch((e) => vivo && setError(e.message))
      .finally(() => vivo && setCargando(false));
    return () => { vivo = false; };
  }, [estado, recarga]);

  // Vuelve a pedir la bandeja (p. ej. tras marcar una atendida). Sin parámetros.
  const cargar = () => setRecarga((n) => n + 1);
  // Cambia el filtro y muestra la carga. Recibe el estado elegido.
  const filtrar = (valor) => { setCargando(true); setEstado(valor); };

  const columnas = [
    { key: "motivo", header: "Motivo", render: (d) => <span className="font-medium text-slate-800">{d.motivo}</span> },
    { key: "origen", header: "Origen", render: (d) => <span className="text-slate-600">{ORIGEN[d.origen] || d.origen}</span> },
    { key: "contacto", header: "Contacto", render: (d) => <span className="text-slate-600">{d.contacto || "—"}</span> },
    { key: "estado", header: "Estado", render: (d) => <Badge tono={d.estado === "PENDIENTE" ? "warning" : "success"}>{d.estado === "PENDIENTE" ? "Pendiente" : `Atendida · ${d.atendida_por || ""}`}</Badge> },
    { key: "creada_en", header: "Recibida", render: (d) => <span className="text-xs text-slate-500 nums">{fmt(d.creada_en)}</span> },
  ];

  return (
    <SectionCard title="Bandeja de derivaciones" subtitle={`${filas.length} conversación(es)`}
      action={
        <Input as="select" value={estado} onChange={(e) => filtrar(e.target.value)} aria-label="Filtrar derivaciones">
          <option value="PENDIENTE">Pendientes</option>
          <option value="ATENDIDA">Atendidas</option>
          <option value="TODAS">Todas</option>
        </Input>
      }>
      {error && <p role="alert" className="mb-3 rounded-xl border border-danger/30 bg-danger-soft px-3 py-2 text-sm text-danger-strong">{error}</p>}
      <DataTable columns={columnas} rows={filas} rowKey={(d) => d.id} loading={cargando} onRowClick={(d) => setAbierta(d.id)}
                 empty={{ icon: Inbox, title: "Bandeja vacía", description: "No hay conversaciones derivadas con este filtro." }} />
      <Modal open={!!abierta} onClose={() => setAbierta(null)} variant="right">
        {abierta && <DetalleDerivacion key={abierta} id={abierta} onCerrar={() => setAbierta(null)} onAtendida={cargar} />}
      </Modal>
    </SectionCard>
  );
}
