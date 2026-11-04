import { useEffect, useState } from "react";
import { Pencil, X, Check, AlertCircle, CalendarDays, PackageSearch, RotateCcw } from "lucide-react";
import SectionCard from "./ui/SectionCard";
import DataTable from "./ui/DataTable";
import Input from "./ui/Input";
import Button from "./ui/Button";
import Modal from "./ui/Modal";
import Badge, { EstadoBadge } from "./ui/Badge";
import { listarSolicitudesRecojo, editarSolicitudRecojo } from "../services/api";

// Fecha local de hoy en formato "AAAA-MM-DD".
const hoyISO = () => new Date().toLocaleDateString("en-CA");

// "AAAA-MM-DD" a "dd/mm/aaaa". Recibe la fecha (o null).
const fechaCorta = (v) => (v ? v.split("-").reverse().join("/") : "—");

// Filtros de la lista: pendientes de ruta (editables) o todas.
const FILTROS = [
  { id: "SOLICITADO", label: "Pendientes de ruta" },
  { id: "", label: "Todas" },
];

// Lista de solicitudes de recojo con edicion antes de armar su ruta (C11-03). Sin props.
export default function SolicitudesRecojo() {
  const [filtro, setFiltro] = useState("SOLICITADO");
  const [solicitudes, setSolicitudes] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [editando, setEditando] = useState(null);
  const [version, setVersion] = useState(0); // fuerza la recarga tras editar

  // Carga la lista cada vez que cambia el filtro o se guarda una edicion.
  useEffect(() => {
    let activo = true;
    listarSolicitudesRecojo(filtro)
      .then((d) => activo && setSolicitudes(d))
      .catch(() => activo && setSolicitudes([]))
      .finally(() => activo && setCargando(false));
    return () => { activo = false; };
  }, [filtro, version]);

  const hoy = hoyISO();
  const columnas = [
    { key: "codigo", header: "Código", render: (s) => <span className="font-medium text-slate-800 nums">{s.codigo || s.id}</span> },
    {
      key: "cliente",
      header: "Cliente",
      render: (s) => (
        <div>
          <p className="text-slate-700">{s.cliente_origen}</p>
          {s.referencia && <p className="text-xs text-slate-400">Ref. {s.referencia}</p>}
        </div>
      ),
    },
    { key: "pedidos", header: "Pedidos", render: (s) => <span className="nums text-slate-600">{s.num_pedidos ?? "—"}</span> },
    {
      key: "fecha",
      header: "Fecha pedida",
      render: (s) => (
        <span className="flex items-center gap-1.5 nums text-slate-600">
          {fechaCorta(s.fecha_programada)}
          {s.estado === "SOLICITADO" && s.fecha_programada && s.fecha_programada < hoy && <Badge tono="danger">Atrasada</Badge>}
        </span>
      ),
    },
    {
      key: "estado",
      header: "Estado",
      render: (s) => (
        <div className="flex flex-wrap items-center gap-1.5">
          <EstadoBadge estado={s.estado} />
          {s.intentos_no_realizados > 0 && (
            <span title={s.motivo_no_realizado || ""}>
              <Badge tono="warning"><RotateCcw size={12} />{s.intentos_no_realizados} visita(s) sin éxito</Badge>
            </span>
          )}
        </div>
      ),
    },
    {
      key: "acciones",
      header: "",
      render: (s) => s.estado === "SOLICITADO" ? (
        <Button variant="ghost" size="sm" icon={Pencil} onClick={(e) => { e.stopPropagation(); setEditando(s); }}>Editar</Button>
      ) : null,
    },
  ];

  return (
    <SectionCard
      title="Solicitudes registradas"
      subtitle="Puedes corregir una solicitud mientras no tenga ruta de recojo asignada."
    >
      <div className="mb-4 flex w-fit gap-1 rounded-xl border border-slate-200 bg-slate-50 p-1">
        {FILTROS.map((f) => (
          <button
            key={f.id || "todas"}
            type="button"
            onClick={() => { setCargando(true); setFiltro(f.id); }}
            className={`rounded-lg px-3.5 py-2 text-sm font-medium transition-colors ${filtro === f.id ? "bg-white text-brand-700 shadow-sm" : "text-slate-500 hover:text-slate-700"}`}
          >
            {f.label}
          </button>
        ))}
      </div>
      <DataTable
        columns={columnas}
        rows={solicitudes}
        rowKey={(s) => s.id}
        loading={cargando}
        onRowClick={(s) => s.estado === "SOLICITADO" && setEditando(s)}
        empty={{ icon: PackageSearch, title: "No hay solicitudes", description: "Las solicitudes aceptadas o registradas aparecerán aquí." }}
      />

      <Modal open={!!editando} onClose={() => setEditando(null)} variant="center">
        {editando && (
          <EditarSolicitud
            key={editando.id}
            solicitud={editando}
            onCerrar={() => setEditando(null)}
            onGuardado={() => { setEditando(null); setVersion((v) => v + 1); }}
          />
        )}
      </Modal>
    </SectionCard>
  );
}

// Formulario de edicion de una solicitud SOLICITADO. Recibe la solicitud y los callbacks.
function EditarSolicitud({ solicitud: s, onCerrar, onGuardado }) {
  const [form, setForm] = useState({
    fecha_programada: s.fecha_programada || "",
    contacto_origen: s.contacto_origen || "",
    referencia: s.referencia || "",
    volumen_estimado_m3: s.volumen_estimado_m3 ?? "",
    direccion_origen: s.direccion_origen || "",
  });
  const [error, setError] = useState("");
  const [guardando, setGuardando] = useState(false);

  // Actualiza un campo del formulario. Recibe el nombre del campo.
  const set = (campo) => (e) => { setForm((f) => ({ ...f, [campo]: e.target.value })); setError(""); };

  // Guarda solo lo que cambio y avisa al padre.
  const guardar = async () => {
    const cambios = {};
    if (form.fecha_programada !== (s.fecha_programada || "")) cambios.fecha_programada = form.fecha_programada || null;
    if (form.contacto_origen.trim() !== (s.contacto_origen || "")) cambios.contacto_origen = form.contacto_origen.trim();
    if (form.referencia.trim() !== (s.referencia || "")) cambios.referencia = form.referencia.trim();
    if (String(form.volumen_estimado_m3) !== String(s.volumen_estimado_m3 ?? "") && form.volumen_estimado_m3 !== "")
      cambios.volumen_estimado_m3 = Number(form.volumen_estimado_m3);
    if (form.direccion_origen.trim() !== (s.direccion_origen || "")) cambios.direccion_origen = form.direccion_origen.trim();
    if (!Object.keys(cambios).length) { onCerrar(); return; }
    setGuardando(true);
    try {
      await editarSolicitudRecojo(s.id, cambios);
      onGuardado();
    } catch (err) {
      setError(err.message);
      setGuardando(false);
    }
  };

  return (
    <>
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <span className="flex h-11 w-11 items-center justify-center rounded-full bg-brand-50 text-brand-700"><CalendarDays size={20} /></span>
          <div>
            <h2 className="font-bold text-slate-900">Editar {s.codigo}</h2>
            <p className="text-sm text-slate-500">{s.cliente_origen} · {s.num_pedidos ?? 0} pedidos</p>
          </div>
        </div>
        <button onClick={onCerrar} aria-label="Cerrar" className="rounded-lg p-2 text-slate-500 hover:bg-slate-100"><X size={20} /></button>
      </div>

      {s.motivo_no_realizado && (
        <div className="mt-4 rounded-xl bg-warning-soft px-3.5 py-3 text-sm text-warning-strong">
          Última visita sin éxito: <b>{s.motivo_no_realizado}</b>. Acuerda una nueva fecha con el cliente.
        </div>
      )}

      <div className="mt-5 space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <Input label="Fecha de recojo" type="date" min={hoyISO()} value={form.fecha_programada} onChange={set("fecha_programada")} />
          <Input label="Volumen estimado (m³)" type="number" min="0" step="0.1" value={form.volumen_estimado_m3} onChange={set("volumen_estimado_m3")} />
        </div>
        <Input label="Contacto en origen" value={form.contacto_origen} onChange={set("contacto_origen")} placeholder="Nombre o teléfono" />
        <Input label="Referencia" value={form.referencia} onChange={set("referencia")} placeholder="Ej. OC-2026-001" />
        <Input label="Dirección de recojo" value={form.direccion_origen} onChange={set("direccion_origen")}
          hint="Si la cambias se vuelve a ubicar en el mapa." />
        {error && (
          <p className="flex items-center gap-2 rounded-xl bg-danger-soft px-3.5 py-3 text-sm text-danger-strong"><AlertCircle size={18} />{error}</p>
        )}
        <div className="flex gap-2">
          <Button variant="secondary" block onClick={onCerrar} disabled={guardando}>Cancelar</Button>
          <Button icon={Check} block onClick={guardar} disabled={guardando}>{guardando ? "Guardando…" : "Guardar"}</Button>
        </div>
      </div>
    </>
  );
}
