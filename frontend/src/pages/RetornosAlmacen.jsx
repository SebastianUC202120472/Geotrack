import { useEffect, useRef, useState } from "react";
import { Undo2, ArrowLeft, ScanLine, CheckCircle2 } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import SectionCard from "../components/ui/SectionCard";
import DataTable from "../components/ui/DataTable";
import Button from "../components/ui/Button";
import Badge from "../components/ui/Badge";
import { listarRutasRetorno, obtenerRetornoRuta, escanearRetorno } from "../services/api";

// CUS-32: logística inversa. Lista de rutas con paquetes FALLIDO; al elegir una se
// escanean los paquetes devueltos y se concilia que todos hayan regresado.
export default function RetornosAlmacen() {
  const [rutas, setRutas] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [seleccion, setSeleccion] = useState(null); // id de ruta en modo retorno

  const cargar = () => {
    listarRutasRetorno().then((d) => setRutas(d)).catch(() => {}).finally(() => setCargando(false));
  };
  useEffect(() => {
    let activo = true;
    listarRutasRetorno().then((d) => activo && setRutas(d)).catch(() => {}).finally(() => activo && setCargando(false));
    return () => { activo = false; };
  }, []);

  if (seleccion != null) {
    return <PanelRetorno rutaId={seleccion} onVolver={() => { setSeleccion(null); setCargando(true); cargar(); }} />;
  }

  const columnas = [
    { key: "codigo", header: "Ruta", render: (r) => <span className="font-medium text-slate-800 nums">{r.codigo || r.ruta_id}</span> },
    { key: "nombre", header: "Nombre", render: (r) => <span className="text-slate-700">{r.nombre}</span> },
    { key: "estado", header: "Estado", render: (r) => <Badge tono="neutral">{r.estado}</Badge> },
    { key: "conteo", header: "Retorno", render: (r) => (
      <span className="text-slate-600 nums">
        {r.conteo.retornados}/{r.conteo.esperados}
        {r.conteo.faltantes > 0 ? ` · faltan ${r.conteo.faltantes}` : ""}
      </span>
    ) },
  ];

  return (
    <div className="space-y-6 p-6 lg:p-8 animate-fade-in">
      <PageHeader titulo="Retornos de Ruta" subtitulo="Recepción de los paquetes no entregados (FALLIDO) que el conductor devuelve al CD." />
      <div className="animate-fade-up">
        <DataTable columns={columnas} rows={rutas} rowKey={(r) => r.ruta_id} loading={cargando}
          empty={{ icon: Undo2, title: "No hay rutas con devoluciones", description: "Aquí aparecen las rutas de entrega que tienen paquetes FALLIDO." }}
          onRowClick={(r) => setSeleccion(r.ruta_id)} />
      </div>
    </div>
  );
}

// Panel de retorno de una ruta: contadores, escaneo y lista de FALLIDO con su estado.
function PanelRetorno({ rutaId, onVolver }) {
  const [det, setDet] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [ultimo, setUltimo] = useState(null);
  const [codigo, setCodigo] = useState("");
  const inputRef = useRef(null);

  const refrescar = () => obtenerRetornoRuta(rutaId).then((d) => setDet(d)).catch(() => {});
  useEffect(() => {
    let activo = true;
    obtenerRetornoRuta(rutaId).then((d) => activo && setDet(d)).catch(() => {}).finally(() => activo && setCargando(false));
    return () => { activo = false; };
  }, [rutaId]);

  useEffect(() => { const t = setTimeout(() => inputRef.current?.focus(), 100); return () => clearTimeout(t); }, [cargando]);

  const escanear = async (e) => {
    e.preventDefault();
    const c = codigo.trim();
    if (!c) return;
    setCodigo("");
    try {
      const r = await escanearRetorno(rutaId, c);
      setUltimo({ resultado: r.resultado, codigo: r.codigo, mensaje: r.mensaje });
      refrescar();
    } catch (err) {
      setUltimo({ resultado: "ERROR", codigo: c, mensaje: err.message });
    } finally {
      inputRef.current?.focus();
    }
  };

  const conteo = det?.conteo ?? { esperados: 0, retornados: 0, faltantes: 0 };
  const colorResultado = (rr) =>
    rr === "RETORNADO" ? "bg-success-soft text-success-strong"
    : rr === "DUPLICADO" ? "bg-warning-soft text-warning-strong"
    : "bg-danger-soft text-danger-strong";

  return (
    <div className="space-y-6 p-6 lg:p-8 animate-fade-in">
      <PageHeader titulo="Retornos de Ruta" subtitulo={det ? `${det.codigo || det.ruta_id} · ${det.nombre}` : "Cargando…"}>
        <Button variant="secondary" icon={ArrowLeft} onClick={onVolver}>Volver</Button>
      </PageHeader>

      <div className="grid grid-cols-3 gap-4 animate-fade-up">
        <Contador etiqueta="Esperados" valor={conteo.esperados} />
        <Contador etiqueta="Retornados" valor={conteo.retornados} tono="success" />
        <Contador etiqueta="Faltantes" valor={conteo.faltantes} tono={conteo.faltantes > 0 ? "warning" : "neutral"} />
      </div>

      <SectionCard title="Escanear devoluciones">
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

      <SectionCard title={`Paquetes FALLIDO (${det?.fallidos?.length ?? 0})`}>
        <div className="max-h-96 divide-y divide-slate-100 overflow-y-auto">
          {(det?.fallidos ?? []).map((f) => (
            <div key={f.pedido_id} className="flex items-center justify-between gap-3 py-2 text-sm">
              <div className="min-w-0">
                <span className="nums font-medium text-slate-700">{f.codigo || f.pedido_id}</span>
                <span className="text-slate-500"> · {f.nombre_destinatario || f.cliente_origen}</span>
              </div>
              {f.retornado_en
                ? <span className="inline-flex items-center gap-1 text-success-strong"><CheckCircle2 size={16} /> retornado</span>
                : <span className="text-warning-strong">pendiente</span>}
            </div>
          ))}
          {(det?.fallidos ?? []).length === 0 && <p className="py-4 text-sm text-slate-400">Esta ruta no tiene paquetes FALLIDO.</p>}
        </div>
      </SectionCard>
    </div>
  );
}

// Tarjeta de contador con tono semántico. Recibe: { etiqueta, valor, tono }.
function Contador({ etiqueta, valor, tono = "neutral" }) {
  const colores = { neutral: "text-slate-700", success: "text-success-strong", warning: "text-warning-strong" };
  return (
    <div className="rounded-card border border-slate-200 bg-white p-4">
      <p className="text-xs text-slate-400">{etiqueta}</p>
      <p className={`text-2xl font-bold nums ${colores[tono]}`}>{valor}</p>
    </div>
  );
}
