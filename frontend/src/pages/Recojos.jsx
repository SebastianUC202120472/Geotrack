import { useEffect, useState } from "react";
import { Inbox, Plus, Route as RouteIcon, X, CheckCircle2, AlertCircle } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import DataTable from "../components/ui/DataTable";
import Input from "../components/ui/Input";
import Button from "../components/ui/Button";
import Modal from "../components/ui/Modal";
import { EstadoBadge } from "../components/ui/Badge";
import { urlMedia, listarRecojos, crearRecojo, asignarRutaRecojo, listarClientes, listarConductores, listarVehiculos } from "../services/api";

const ESTADOS = ["", "SOLICITADO", "ASIGNADO", "EN_RUTA", "RECOGIDO"];

// Módulo Inbound de recojos (CUS-10/11): alta de solicitudes y armado de rutas de recojo.
export default function Recojos() {
  const [recojos, setRecojos] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [filtro, setFiltro] = useState("");
  const [clientes, setClientes] = useState([]);
  const [conductores, setConductores] = useState([]);
  const [vehiculos, setVehiculos] = useState([]);
  const [nueva, setNueva] = useState(false);
  const [modalRuta, setModalRuta] = useState(false);
  const [detalle, setDetalle] = useState(null);

  // Carga la lista según el filtro. Los setState van en callbacks de promesa para no
  // disparar el lint "setState síncrono en effect".
  const cargar = (estado) => {
    listarRecojos(estado || undefined)
      .then((d) => setRecojos(d))
      .catch(() => {})
      .finally(() => setCargando(false));
  };

  useEffect(() => {
    let activo = true;
    listarRecojos(filtro || undefined)
      .then((d) => activo && setRecojos(d))
      .catch(() => {})
      .finally(() => activo && setCargando(false));
    return () => { activo = false; };
  }, [filtro]);

  // Catálogos para los formularios (clientes, conductores, vehículos).
  useEffect(() => {
    let activo = true;
    listarClientes().then((d) => activo && setClientes(d)).catch(() => {});
    listarConductores().then((d) => activo && setConductores(d)).catch(() => {});
    listarVehiculos().then((d) => activo && setVehiculos(d)).catch(() => {});
    return () => { activo = false; };
  }, []);

  const columnas = [
    { key: "codigo", header: "Código", render: (r) => <span className="font-medium text-slate-800 nums">{r.codigo || "—"}</span> },
    { key: "cliente_origen", header: "Cliente", render: (r) => <span className="text-slate-700">{r.cliente_origen}</span> },
    { key: "direccion_origen", header: "Origen", render: (r) => <span className="text-slate-600">{r.direccion_origen}</span> },
    { key: "distrito", header: "Distrito", render: (r) => <span className="text-slate-600">{r.distrito || "—"}</span> },
    { key: "volumen", header: "Vol. (m³)", render: (r) => <span className="text-slate-600 nums">{r.volumen_estimado_m3 ?? "—"}</span> },
    { key: "estado", header: "Estado", render: (r) => <EstadoBadge estado={r.estado} /> },
  ];

  return (
    <div className="space-y-6 p-6 lg:p-8 animate-fade-in">
      <PageHeader titulo="Recojos" subtitulo="Solicitudes de recojo (inbound) y armado de rutas de recolección.">
        <Button variant="secondary" icon={RouteIcon} onClick={() => setModalRuta(true)}>Crear ruta de recojo</Button>
        <Button icon={Plus} onClick={() => setNueva(true)}>Nueva solicitud</Button>
      </PageHeader>

      <div className="flex flex-wrap gap-2 animate-fade-up">
        {ESTADOS.map((e) => (
          <button key={e || "todos"} onClick={() => { setCargando(true); setFiltro(e); }}
            className={`rounded-full px-3.5 py-1.5 text-sm font-medium transition-colors ${filtro === e ? "bg-brand-600 text-white" : "bg-white text-slate-600 border border-slate-200 hover:bg-slate-50"}`}>
            {e ? e.replaceAll("_", " ").toLowerCase() : "todos"}
          </button>
        ))}
      </div>

      <div className="animate-fade-up" style={{ animationDelay: "60ms" }}>
        <DataTable columns={columnas} rows={recojos} rowKey={(r) => r.id} loading={cargando}
          empty={{ icon: Inbox, title: "Aún no hay solicitudes de recojo", description: "Crea una solicitud con el botón \"Nueva solicitud\"." }}
          onRowClick={(r) => setDetalle(r)} />
      </div>

      {/* CUS-10: nueva solicitud */}
      <Modal open={nueva} onClose={() => setNueva(false)} variant="right" className="max-w-lg">
        <FormNuevaSolicitud clientes={clientes}
          onCerrar={() => setNueva(false)}
          onCreado={() => { setNueva(false); cargar(filtro); }} />
      </Modal>

      {/* CUS-11: crear ruta de recojo */}
      <Modal open={modalRuta} onClose={() => setModalRuta(false)} variant="right" className="max-w-lg">
        <FormRutaRecojo recojos={recojos.filter((r) => r.estado === "SOLICITADO")} conductores={conductores} vehiculos={vehiculos}
          onCerrar={() => setModalRuta(false)}
          onCreada={() => { setModalRuta(false); cargar(filtro); }} />
      </Modal>

      {/* Detalle */}
      <Modal open={!!detalle} onClose={() => setDetalle(null)} variant="center">
        {detalle && <DetalleRecojo recojo={detalle} onCerrar={() => setDetalle(null)} />}
      </Modal>
    </div>
  );
}

// Formulario de alta (CUS-10). Recibe: clientes, onCerrar, onCreado.
function FormNuevaSolicitud({ clientes, onCerrar, onCreado }) {
  const [form, setForm] = useState({ cliente_id: "", direccion_origen: "", volumen_estimado_m3: "", contacto_origen: "", referencia: "" });
  const [aviso, setAviso] = useState(null);
  const [guardando, setGuardando] = useState(false);

  const enviar = async (e) => {
    e.preventDefault();
    if (!form.cliente_id) { setAviso({ ok: false, texto: "Elige un cliente." }); return; }
    if (form.direccion_origen.trim().length < 4) { setAviso({ ok: false, texto: "Indica la dirección de origen." }); return; }
    setGuardando(true); setAviso(null);
    try {
      const r = await crearRecojo({
        cliente_id: Number(form.cliente_id),
        direccion_origen: form.direccion_origen.trim(),
        volumen_estimado_m3: form.volumen_estimado_m3 ? Number(form.volumen_estimado_m3) : null,
        contacto_origen: form.contacto_origen.trim() || null,
        referencia: form.referencia.trim() || null,
      });
      setAviso({ ok: true, texto: `Solicitud ${r.codigo || ""} creada.` });
      setTimeout(onCreado, 500);
    } catch (err) {
      setAviso({ ok: false, texto: err.message }); setGuardando(false);
    }
  };

  return (
    <div className="p-6">
      <div className="flex items-start justify-between">
        <h2 className="text-lg font-bold text-slate-900">Nueva solicitud de recojo</h2>
        <button onClick={onCerrar} aria-label="Cerrar" className="rounded-lg p-2 text-slate-500 hover:bg-slate-100"><X size={20} /></button>
      </div>
      <form onSubmit={enviar} noValidate className="mt-6 space-y-4">
        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700">Cliente</label>
          <select value={form.cliente_id} onChange={(e) => setForm((f) => ({ ...f, cliente_id: e.target.value }))}
            className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm">
            <option value="">— Selecciona —</option>
            {clientes.map((c) => <option key={c.id} value={c.id}>{c.razon_social}</option>)}
          </select>
        </div>
        <Input label="Dirección de origen" value={form.direccion_origen}
          onChange={(e) => setForm((f) => ({ ...f, direccion_origen: e.target.value }))}
          placeholder="Av. ..., Distrito" hint="Se geocodifica al guardar (separa el distrito con una coma)" />
        <Input label="Volumen estimado (m³)" type="number" value={form.volumen_estimado_m3}
          onChange={(e) => setForm((f) => ({ ...f, volumen_estimado_m3: e.target.value }))} hint="Opcional" />
        <Input label="Contacto en origen" value={form.contacto_origen}
          onChange={(e) => setForm((f) => ({ ...f, contacto_origen: e.target.value }))} hint="Opcional" />
        <Input label="Referencia" value={form.referencia}
          onChange={(e) => setForm((f) => ({ ...f, referencia: e.target.value }))} hint="Nº de aviso / nota (opcional)" />
        <Button type="submit" icon={Plus} block disabled={guardando}>{guardando ? "Guardando…" : "Crear solicitud"}</Button>
        {aviso && (
          <div className={`flex items-center gap-2 rounded-xl px-3.5 py-3 text-sm ${aviso.ok ? "bg-success-soft text-success-strong" : "bg-danger-soft text-danger-strong"}`}>
            {aviso.ok ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}<span>{aviso.texto}</span>
          </div>
        )}
      </form>
    </div>
  );
}

// Formulario de armado de ruta (CUS-11). Recibe: recojos SOLICITADO, conductores, vehiculos.
// conductor_id usa c.usuario_id (igual que AsignacionBloque.jsx que ya envía ese campo al backend).
function FormRutaRecojo({ recojos, conductores, vehiculos, onCerrar, onCreada }) {
  const [seleccion, setSeleccion] = useState([]);
  const [conductorId, setConductorId] = useState("");
  const [placa, setPlaca] = useState("");
  const [nombre, setNombre] = useState("");
  const [aviso, setAviso] = useState(null);
  const [guardando, setGuardando] = useState(false);

  const alternar = (id) => setSeleccion((s) => s.includes(id) ? s.filter((x) => x !== id) : [...s, id]);

  const enviar = async () => {
    if (!seleccion.length) { setAviso({ ok: false, texto: "Selecciona al menos una solicitud." }); return; }
    if (!conductorId) { setAviso({ ok: false, texto: "Elige un conductor." }); return; }
    if (!placa) { setAviso({ ok: false, texto: "Elige un vehículo." }); return; }
    setGuardando(true); setAviso(null);
    try {
      const r = await asignarRutaRecojo({ recojo_ids: seleccion, conductor_id: Number(conductorId), vehiculo_placa: placa, nombre_ruta: nombre.trim() || null });
      setAviso({ ok: true, texto: r.mensaje });
      setTimeout(onCreada, 600);
    } catch (err) { setAviso({ ok: false, texto: err.message }); setGuardando(false); }
  };

  return (
    <div className="p-6">
      <div className="flex items-start justify-between">
        <h2 className="text-lg font-bold text-slate-900">Crear ruta de recojo</h2>
        <button onClick={onCerrar} aria-label="Cerrar" className="rounded-lg p-2 text-slate-500 hover:bg-slate-100"><X size={20} /></button>
      </div>

      <p className="mt-4 text-sm text-slate-500">Solicitudes disponibles (SOLICITADO)</p>
      <div className="mt-2 max-h-64 space-y-2 overflow-y-auto">
        {recojos.length === 0 && <p className="text-sm text-slate-400">No hay solicitudes disponibles.</p>}
        {recojos.map((r) => (
          <label key={r.id} className="flex cursor-pointer items-center gap-3 rounded-xl border border-slate-200 px-3 py-2 text-sm hover:bg-slate-50">
            <input type="checkbox" checked={seleccion.includes(r.id)} onChange={() => alternar(r.id)} />
            <span className="font-medium text-slate-700">{r.codigo}</span>
            <span className="text-slate-500">· {r.cliente_origen} · {r.distrito || "s/zona"}</span>
          </label>
        ))}
      </div>

      <div className="mt-4 space-y-4">
        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700">Conductor</label>
          <select value={conductorId} onChange={(e) => setConductorId(e.target.value)} className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm">
            <option value="">— Selecciona —</option>
            {conductores.map((c) => {
              const id = c.usuario_id ?? c.id;
              return <option key={id} value={id}>{c.nombre ?? c.correo ?? `Conductor ${id}`}</option>;
            })}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700">Vehículo</label>
          <select value={placa} onChange={(e) => setPlaca(e.target.value)} className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm">
            <option value="">— Selecciona —</option>
            {vehiculos.map((v) => <option key={v.id ?? v.placa} value={v.placa}>{v.placa}{v.codigo ? ` · ${v.codigo}` : ""}</option>)}
          </select>
        </div>
        <Input label="Nombre de la ruta" value={nombre} onChange={(e) => setNombre(e.target.value)} hint={'Opcional (por defecto: "Recojo <distrito>")'} />
        <Button icon={RouteIcon} block disabled={guardando} onClick={enviar}>{guardando ? "Creando…" : "Crear ruta de recojo"}</Button>
        {aviso && (
          <div className={`flex items-center gap-2 rounded-xl px-3.5 py-3 text-sm ${aviso.ok ? "bg-success-soft text-success-strong" : "bg-danger-soft text-danger-strong"}`}>
            {aviso.ok ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}<span>{aviso.texto}</span>
          </div>
        )}
      </div>
    </div>
  );
}

// Detalle de una solicitud (incluye la recepción si ya está RECOGIDO).
function DetalleRecojo({ recojo: r, onCerrar }) {
  return (
    <>
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <span className="flex h-12 w-12 items-center justify-center rounded-full bg-brand-600 text-white"><Inbox size={22} /></span>
          <div>
            <h2 className="font-bold text-slate-900">{r.codigo || "Recojo"}</h2>
            <p className="text-sm text-slate-500">{r.cliente_origen}</p>
          </div>
        </div>
        <button onClick={onCerrar} aria-label="Cerrar" className="rounded-lg p-2 text-slate-500 hover:bg-slate-100"><X size={20} /></button>
      </div>

      <div className="mt-4"><EstadoBadge estado={r.estado} /></div>

      <div className="mt-4 space-y-3 text-sm">
        <Fila etiqueta="Origen" valor={r.direccion_origen} />
        <Fila etiqueta="Distrito" valor={r.distrito || "—"} />
        <Fila etiqueta="Volumen estimado (m³)" valor={r.volumen_estimado_m3 ?? "—"} />
        <Fila etiqueta="Contacto" valor={r.contacto_origen || "—"} />
        <Fila etiqueta="Referencia" valor={r.referencia || "—"} />
        {r.estado === "RECOGIDO" && (
          <>
            <Fila etiqueta="Cantidad declarada" valor={r.cantidad_declarada ?? "—"} />
            {urlMedia(r.url_guia) && (
              <div>
                <p className="text-xs text-slate-400">Guía de Remisión</p>
                <img src={urlMedia(r.url_guia)} alt="Guía de Remisión" className="mt-1 max-h-72 rounded-xl border border-slate-200" />
              </div>
            )}
          </>
        )}
      </div>
    </>
  );
}

function Fila({ etiqueta, valor }) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-xl bg-slate-50 px-4 py-2.5">
      <span className="text-xs text-slate-400">{etiqueta}</span>
      <span className="font-medium text-slate-700">{valor}</span>
    </div>
  );
}
