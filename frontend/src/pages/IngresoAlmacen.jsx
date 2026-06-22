import { useEffect, useRef, useState } from "react";
import { PackageCheck, ArrowLeft, Upload, CheckCircle2, AlertCircle, ScanLine } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import SectionCard from "../components/ui/SectionCard";
import DataTable from "../components/ui/DataTable";
import Button from "../components/ui/Button";
import { EstadoBadge } from "../components/ui/Badge";
import { listarRecojosAlmacen, obtenerConciliacion, escanearPaquete, cerrarIngreso, importarTrama } from "../services/api";

// CUS-14: ingreso por escaneo. Lista de recojos por ingresar; al elegir uno se entra
// al panel de ingreso (importar trama + escanear + conciliar + cerrar).
export default function IngresoAlmacen() {
  const [recojos, setRecojos] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [seleccion, setSeleccion] = useState(null); // id de recojo en modo ingreso

  // Recarga la lista. setState en callbacks de promesa (lint-safe).
  const cargar = () => {
    listarRecojosAlmacen().then((d) => setRecojos(d)).catch(() => {}).finally(() => setCargando(false));
  };
  useEffect(() => {
    let activo = true;
    listarRecojosAlmacen().then((d) => activo && setRecojos(d)).catch(() => {}).finally(() => activo && setCargando(false));
    return () => { activo = false; };
  }, []);

  if (seleccion != null) {
    return <PanelIngreso recojoId={seleccion} onVolver={() => { setSeleccion(null); setCargando(true); cargar(); }} />;
  }

  const columnas = [
    { key: "codigo", header: "Código", render: (r) => <span className="font-medium text-slate-800 nums">{r.codigo || "—"}</span> },
    { key: "cliente_origen", header: "Cliente", render: (r) => <span className="text-slate-700">{r.cliente_origen}</span> },
    { key: "estado", header: "Estado", render: (r) => <EstadoBadge estado={r.estado} /> },
    { key: "conteo", header: "Conciliación", render: (r) => (
      <span className="text-slate-600 nums">
        {r.conteo.ingresados}/{r.conteo.esperados}
        {r.conteo.faltantes > 0 ? ` · faltan ${r.conteo.faltantes}` : ""}
        {r.conteo.desconocidos > 0 ? ` · ${r.conteo.desconocidos} desc.` : ""}
      </span>
    ) },
  ];

  return (
    <div className="space-y-6 p-6 lg:p-8 animate-fade-in">
      <PageHeader titulo="Ingreso a Almacén" subtitulo="Escanea los paquetes recogidos y concílialos contra la trama del retail." />
      <div className="animate-fade-up">
        <DataTable columns={columnas} rows={recojos} rowKey={(r) => r.id} loading={cargando}
          empty={{ icon: PackageCheck, title: "No hay recojos por ingresar", description: "Aquí aparecen los recojos en estado RECOGIDO." }}
          onRowClick={(r) => setSeleccion(r.id)} />
      </div>
    </div>
  );
}

// Panel de ingreso de un recojo: contadores, importar trama (si no hay), escanear y cerrar.
function PanelIngreso({ recojoId, onVolver }) {
  const [conc, setConc] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [ultimo, setUltimo] = useState(null);   // último resultado de escaneo
  const [codigo, setCodigo] = useState("");
  const [trabajando, setTrabajando] = useState(false);
  const [aviso, setAviso] = useState(null);
  const inputRef = useRef(null);

  const refrescar = () => obtenerConciliacion(recojoId).then((d) => setConc(d)).catch(() => {});
  useEffect(() => {
    let activo = true;
    obtenerConciliacion(recojoId).then((d) => activo && setConc(d)).catch(() => {}).finally(() => activo && setCargando(false));
    return () => { activo = false; };
  }, [recojoId]);

  // Enfoca el campo de escaneo tras cargar (la pistola teclea directo + Enter).
  useEffect(() => { const t = setTimeout(() => inputRef.current?.focus(), 100); return () => clearTimeout(t); }, [cargando]);

  const escanear = async (e) => {
    e.preventDefault();
    const c = codigo.trim();
    if (!c) return;
    setCodigo("");
    try {
      const r = await escanearPaquete(recojoId, c);
      setUltimo({ resultado: r.resultado, codigo: r.codigo, mensaje: r.mensaje });
      refrescar();
    } catch (err) {
      setUltimo({ resultado: "ERROR", codigo: c, mensaje: err.message });
    } finally {
      inputRef.current?.focus();
    }
  };

  const subirTrama = async (e) => {
    const archivo = e.target.files?.[0];
    e.target.value = "";
    if (!archivo) return;
    setTrabajando(true); setAviso(null);
    try {
      const r = await importarTrama(recojoId, archivo);
      setAviso({ ok: true, texto: r.mensaje });
      refrescar();
    } catch (err) { setAviso({ ok: false, texto: err.message }); }
    finally { setTrabajando(false); }
  };

  const cerrar = async () => {
    setTrabajando(true); setAviso(null);
    try { const r = await cerrarIngreso(recojoId); setAviso({ ok: true, texto: r.mensaje }); refrescar(); }
    catch (err) { setAviso({ ok: false, texto: err.message }); }
    finally { setTrabajando(false); }
  };

  const conteo = conc?.conteo ?? { esperados: 0, ingresados: 0, faltantes: 0, desconocidos: 0 };
  const sinTrama = conteo.esperados === 0;
  const colorResultado = (rr) =>
    rr === "INGRESADO" ? "bg-success-soft text-success-strong"
    : rr === "DUPLICADO" ? "bg-warning-soft text-warning-strong"
    : "bg-danger-soft text-danger-strong";

  return (
    <div className="space-y-6 p-6 lg:p-8 animate-fade-in">
      <PageHeader titulo="Ingreso a Almacén" subtitulo={conc ? `Recojo ${conc.recojo_id} · ${conc.estado_recojo}` : "Cargando…"}>
        <Button variant="secondary" icon={ArrowLeft} onClick={onVolver}>Volver</Button>
      </PageHeader>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 animate-fade-up">
        <Contador etiqueta="Esperados" valor={conteo.esperados} />
        <Contador etiqueta="Ingresados" valor={conteo.ingresados} tono="success" />
        <Contador etiqueta="Faltantes" valor={conteo.faltantes} tono={conteo.faltantes > 0 ? "warning" : "neutral"} />
        <Contador etiqueta="Desconocidos" valor={conteo.desconocidos} tono={conteo.desconocidos > 0 ? "danger" : "neutral"} />
      </div>

      {sinTrama ? (
        <SectionCard title="Importar trama">
          <p className="mb-3 text-sm text-slate-500">Sube el Excel con los códigos esperados del recojo (columna <code>codigo</code>).</p>
          <label className="inline-flex">
            <input type="file" accept=".xlsx" className="hidden" onChange={subirTrama} disabled={trabajando} />
            <span className="inline-flex cursor-pointer items-center gap-2 rounded-xl bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-brand-700">
              <Upload size={18} /> {trabajando ? "Importando…" : "Importar trama (.xlsx)"}
            </span>
          </label>
        </SectionCard>
      ) : (
        <SectionCard title="Escanear paquetes">
          <form onSubmit={escanear} className="flex gap-2">
            <input ref={inputRef} value={codigo} onChange={(e) => setCodigo(e.target.value)} autoFocus
              placeholder="Escanea o teclea el código y pulsa Enter"
              className="flex-1 rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm" />
            <Button type="submit" icon={ScanLine}>Escanear</Button>
          </form>
          {ultimo && (
            <div className={`mt-3 flex items-center gap-2 rounded-xl px-3.5 py-3 text-sm ${colorResultado(ultimo.resultado)}`}>
              <span className="font-semibold nums">{ultimo.codigo}</span><span>·</span><span>{ultimo.mensaje}</span>
            </div>
          )}
        </SectionCard>
      )}

      {aviso && (
        <div className={`flex items-center gap-2 rounded-xl px-3.5 py-3 text-sm ${aviso.ok ? "bg-success-soft text-success-strong" : "bg-danger-soft text-danger-strong"}`}>
          {aviso.ok ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}<span>{aviso.texto}</span>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <SectionCard title={`Trama (${conc?.esperados?.length ?? 0})`}>
          <div className="max-h-80 divide-y divide-slate-100 overflow-y-auto">
            {(conc?.esperados ?? []).map((p) => (
              <div key={p.codigo} className="flex items-center justify-between py-2 text-sm">
                <span className="nums text-slate-700">{p.codigo}</span>
                <EstadoBadge estado={p.estado} />
              </div>
            ))}
            {(conc?.esperados ?? []).length === 0 && <p className="py-4 text-sm text-slate-400">Sin trama importada.</p>}
          </div>
        </SectionCard>
        <SectionCard title={`Desconocidos (${conc?.desconocidos?.length ?? 0})`}>
          <div className="max-h-80 divide-y divide-slate-100 overflow-y-auto">
            {(conc?.desconocidos ?? []).map((c) => <div key={c} className="py-2 text-sm nums text-danger-strong">{c}</div>)}
            {(conc?.desconocidos ?? []).length === 0 && <p className="py-4 text-sm text-slate-400">Ninguno.</p>}
          </div>
        </SectionCard>
      </div>

      {!sinTrama && conc?.estado_recojo !== "INGRESADO" && (
        <Button onClick={cerrar} disabled={trabajando}>{trabajando ? "Cerrando…" : "Cerrar ingreso"}</Button>
      )}
    </div>
  );
}

// Tarjeta de contador con tono semántico. Recibe: { etiqueta, valor, tono }.
function Contador({ etiqueta, valor, tono = "neutral" }) {
  const colores = { neutral: "text-slate-700", success: "text-success-strong", warning: "text-warning-strong", danger: "text-danger-strong" };
  return (
    <div className="rounded-card border border-slate-200 bg-white p-4">
      <p className="text-xs text-slate-400">{etiqueta}</p>
      <p className={`text-2xl font-bold nums ${colores[tono]}`}>{valor}</p>
    </div>
  );
}
