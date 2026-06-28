import { useEffect, useMemo, useState } from "react";
import { Building2, Plus, CheckCircle2, AlertCircle, X, Pencil, Trash2, Check, IdCard, Mail, MapPin } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import KpiCard from "../components/ui/KpiCard";
import DataTable from "../components/ui/DataTable";
import SectionCard from "../components/ui/SectionCard";
import Input from "../components/ui/Input";
import Button from "../components/ui/Button";
import Modal from "../components/ui/Modal";
import { listarClientes, crearCliente, actualizarCliente, eliminarCliente } from "../services/api";

// Administración de empresas cliente (CUS-07): alta, edición y baja.
// Al importar pedidos el cliente debe estar registrado aquí (ya no se crea solo).
export default function Clientes() {
  const [clientes, setClientes] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [seleccionado, setSeleccionado] = useState(null);
  // Modo con el que se abre el modal: "ver" (click en fila), "editar" o "confirmar" (botones de acción)
  const [modoInicial, setModoInicial] = useState("ver");

  const [form, setForm] = useState({ razon_social: "", identificador_unico: "", contacto: "", direccion_origen: "" });
  const [error, setError] = useState("");
  const [aviso, setAviso] = useState(null);
  const [guardando, setGuardando] = useState(false);

  // No se hace setCargando(true) aquí: el estado inicia en true y, al refrescar tras
  // crear/editar, los setState ocurren en los callbacks de la promesa (evita el error
  // de lint "setState síncrono en effect" al llamar cargar() desde el useEffect).
  const cargar = async () => {
    try {
      setClientes(await listarClientes());
    } catch (err) {
      console.error("No se pudo cargar clientes:", err.message);
    } finally {
      setCargando(false);
    }
  };

  // Carga inicial: los setState van en los callbacks de la promesa (no en el cuerpo
  // del efecto) para no disparar el lint "setState síncrono en effect".
  useEffect(() => {
    let activo = true;
    listarClientes()
      .then((d) => activo && setClientes(d))
      .catch(() => {})
      .finally(() => activo && setCargando(false));
    return () => { activo = false; };
  }, []);

  const kpis = useMemo(() => ({
    total: clientes.length,
    conRuc: clientes.filter((c) => c.identificador_unico).length,
  }), [clientes]);

  const registrar = async (e) => {
    e.preventDefault();
    setAviso(null);
    if (form.razon_social.trim().length < 3) {
      setError("La razón social debe tener al menos 3 caracteres.");
      return;
    }
    setError("");
    setGuardando(true);
    try {
      const c = await crearCliente({
        razon_social: form.razon_social.trim(),
        identificador_unico: form.identificador_unico.trim() || null,
        contacto: form.contacto.trim() || null,
        direccion_origen: form.direccion_origen.trim(),
      });
      setAviso({ ok: true, texto: `Cliente ${c.razon_social} registrado (${c.codigo || "—"}).` });
      setForm({ razon_social: "", identificador_unico: "", contacto: "", direccion_origen: "" });
      cargar();
    } catch (err) {
      setAviso({ ok: false, texto: err.message });
    } finally {
      setGuardando(false);
    }
  };

  const columnas = [
    { key: "codigo", header: "Código", render: (c) => <span className="font-medium text-slate-800 nums">{c.codigo || "—"}</span> },
    { key: "razon_social", header: "Razón social", render: (c) => <span className="text-slate-700">{c.razon_social}</span> },
    { key: "identificador_unico", header: "RUC", render: (c) => <span className="text-slate-600 nums">{c.identificador_unico || "—"}</span> },
    { key: "contacto", header: "Contacto", render: (c) => <span className="text-slate-600">{c.contacto || "—"}</span> },
    // Columna de acciones: abre el modal directamente en el modo correspondiente
    {
      key: "acciones",
      header: "",
      render: (c) => (
        <div className="flex justify-end gap-1">
          <Button variant="ghost" size="sm" icon={Pencil}
            onClick={(e) => { e.stopPropagation(); setModoInicial("editar"); setSeleccionado(c); }}>Editar</Button>
          <Button variant="ghost" size="sm" icon={Trash2}
            onClick={(e) => { e.stopPropagation(); setModoInicial("confirmar"); setSeleccionado(c); }}>Baja</Button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6 p-6 lg:p-8 animate-fade-in">
      <PageHeader titulo="Clientes Corporativos" subtitulo="Registra y administra las empresas a las que prestas el servicio." />

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 animate-fade-up">
        <KpiCard label="Total" value={kpis.total} icon={Building2} tone="brand" />
        <KpiCard label="Con RUC" value={kpis.conRuc} icon={IdCard} tone="info" />
      </div>

      <div className="grid gap-6 lg:grid-cols-3 animate-fade-up" style={{ animationDelay: "60ms" }}>
        <SectionCard title="Registrar cliente" className="lg:col-span-1">
          <form onSubmit={registrar} noValidate className="space-y-4">
            <Input label="Razón social" required value={form.razon_social}
              onChange={(e) => { setForm((f) => ({ ...f, razon_social: e.target.value })); setError(""); }}
              placeholder="Ej. Ripley S.A." error={error} hint="Nombre legal de la empresa" />
            <Input label="RUC" value={form.identificador_unico}
              onChange={(e) => setForm((f) => ({ ...f, identificador_unico: e.target.value }))}
              placeholder="20123456789" hint="Identificador único (opcional)" />
            <Input label="Contacto" value={form.contacto}
              onChange={(e) => setForm((f) => ({ ...f, contacto: e.target.value }))}
              placeholder="correo / teléfono" hint="Opcional" />
            <Input label="Dirección de recojo" required value={form.direccion_origen}
              onChange={(e) => setForm((f) => ({ ...f, direccion_origen: e.target.value }))}
              placeholder="Ej. Av. Primavera 123, Miraflores"
              hint="Separa el distrito con una coma. Se geocodifica al guardar." />
            <Button type="submit" icon={Plus} block disabled={guardando}>{guardando ? "Registrando…" : "Registrar cliente"}</Button>
            {aviso && (
              <div className={`flex items-center gap-2 rounded-xl px-3.5 py-3 text-sm ${aviso.ok ? "bg-success-soft text-success-strong" : "bg-danger-soft text-danger-strong"}`}>
                {aviso.ok ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}
                <span>{aviso.texto}</span>
              </div>
            )}
          </form>
        </SectionCard>

        <div className="lg:col-span-2">
          <DataTable columns={columnas} rows={clientes} rowKey={(c) => c.id} loading={cargando}
            empty={{ icon: Building2, title: "Aún no hay clientes", description: "Usa el formulario para registrar la primera empresa." }}
            onRowClick={(c) => { setModoInicial("ver"); setSeleccionado(c); }} />
        </div>
      </div>

      <Modal open={!!seleccionado} onClose={() => { setSeleccionado(null); setModoInicial("ver"); }} variant="center">
        {seleccionado && (
          <DetalleCliente cliente={seleccionado} modoInicial={modoInicial}
            onCerrar={() => { setSeleccionado(null); setModoInicial("ver"); }}
            onCambios={() => { setSeleccionado(null); setModoInicial("ver"); cargar(); }} />
        )}
      </Modal>
    </div>
  );
}

// Detalle del cliente con modos ver / editar / confirmar (baja). Acepta modoInicial
// para abrir directamente en el modo solicitado desde los botones de acción de la fila.
function DetalleCliente({ cliente: c, onCerrar, onCambios, modoInicial = "ver" }) {
  const [modo, setModo] = useState(modoInicial);
  const [form, setForm] = useState({ razon_social: c.razon_social || "", identificador_unico: c.identificador_unico || "", contacto: c.contacto || "", direccion_origen: c.direccion_origen || "" });
  const [aviso, setAviso] = useState(null);
  const [trabajando, setTrabajando] = useState(false);

  const guardar = async () => {
    if (form.razon_social.trim().length < 3) { setAviso({ texto: "La razón social debe tener al menos 3 caracteres." }); return; }
    setTrabajando(true); setAviso(null);
    try {
      await actualizarCliente(c.id, {
        razon_social: form.razon_social.trim(),
        identificador_unico: form.identificador_unico.trim() || null,
        contacto: form.contacto.trim() || null,
        direccion_origen: form.direccion_origen.trim() || null,
      });
      onCambios();
    } catch (err) { setAviso({ texto: err.message }); setTrabajando(false); }
  };

  const eliminar = async () => {
    setTrabajando(true); setAviso(null);
    try { await eliminarCliente(c.id); onCambios(); }
    catch (err) { setAviso({ texto: err.message }); setTrabajando(false); setModo("ver"); }
  };

  return (
    <>
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <span className="flex h-12 w-12 items-center justify-center rounded-full bg-brand-600 text-white"><Building2 size={22} /></span>
          <div>
            <h2 className="font-bold text-slate-900">{c.razon_social}</h2>
            <p className="text-sm text-slate-500 nums">{c.codigo}</p>
          </div>
        </div>
        <button onClick={onCerrar} aria-label="Cerrar" className="rounded-lg p-2 text-slate-500 hover:bg-slate-100"><X size={20} /></button>
      </div>

      {aviso && (
        <div className="mt-4 flex items-center gap-2 rounded-xl bg-danger-soft px-3.5 py-3 text-sm text-danger-strong">
          <AlertCircle size={18} /> <span>{aviso.texto}</span>
        </div>
      )}

      {modo === "ver" && (
        <>
          <div className="mt-6 space-y-3">
            <Dato icono={IdCard} etiqueta="RUC" valor={c.identificador_unico || "—"} />
            <Dato icono={Mail} etiqueta="Contacto" valor={c.contacto || "—"} />
            <Dato icono={MapPin} etiqueta="Dirección de recojo" valor={c.direccion_origen || "—"} />
          </div>
          <div className="mt-6 flex gap-2">
            <Button variant="secondary" icon={Pencil} block onClick={() => { setAviso(null); setModo("editar"); }}>Editar</Button>
            <Button variant="danger" icon={Trash2} block onClick={() => { setAviso(null); setModo("confirmar"); }}>Eliminar</Button>
          </div>
        </>
      )}

      {modo === "editar" && (
        <div className="mt-6 space-y-4">
          <Input label="Razón social" value={form.razon_social} onChange={(e) => setForm((f) => ({ ...f, razon_social: e.target.value }))} />
          <Input label="RUC" value={form.identificador_unico} onChange={(e) => setForm((f) => ({ ...f, identificador_unico: e.target.value }))} />
          <Input label="Contacto" value={form.contacto} onChange={(e) => setForm((f) => ({ ...f, contacto: e.target.value }))} />
          <Input label="Dirección de recojo" value={form.direccion_origen}
            onChange={(e) => setForm((f) => ({ ...f, direccion_origen: e.target.value }))}
            placeholder="Ej. Av. Primavera 123, Miraflores"
            hint="Separa el distrito con una coma. Se geocodifica al guardar." />
          <div className="flex gap-2">
            <Button variant="secondary" block onClick={() => setModo("ver")} disabled={trabajando}>Cancelar</Button>
            <Button icon={Check} block onClick={guardar} disabled={trabajando}>{trabajando ? "Guardando…" : "Guardar"}</Button>
          </div>
        </div>
      )}

      {modo === "confirmar" && (
        <div className="mt-6 space-y-4">
          <div className="flex items-start gap-3 rounded-xl bg-danger-soft px-4 py-3 text-sm text-danger-strong">
            <AlertCircle size={20} className="shrink-0" />
            <span>¿Dar de baja a <b>{c.razon_social}</b>? Dejará de aparecer en la lista (su historial se conserva).</span>
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" block onClick={() => setModo("ver")} disabled={trabajando}>Cancelar</Button>
            <Button variant="danger" icon={Trash2} block onClick={eliminar} disabled={trabajando}>{trabajando ? "Eliminando…" : "Sí, eliminar"}</Button>
          </div>
        </div>
      )}
    </>
  );
}

function Dato({ etiqueta, valor, icono: Icono }) {
  return (
    <div className="flex items-center gap-3 rounded-xl bg-slate-50 px-4 py-3 text-sm">
      <Icono size={18} className="text-slate-400" />
      <div>
        <p className="text-xs text-slate-400">{etiqueta}</p>
        <p className="font-medium text-slate-700">{valor}</p>
      </div>
    </div>
  );
}
