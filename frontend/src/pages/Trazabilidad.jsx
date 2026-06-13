import { useState } from "react";
import { Search, Package, MapPin, Loader2, AlertCircle } from "lucide-react";
import Header from "../components/Header";
import { obtenerHistorial } from "../services/api";

// Trazabilidad de un paquete (CUS-35). El admin busca por código (PD-001) y ve
// la ficha del pedido más su línea de tiempo completa de eventos.
export default function Trazabilidad() {
  const [codigo, setCodigo] = useState("");
  const [historial, setHistorial] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState("");

  const buscar = async (e) => {
    e.preventDefault();
    if (!codigo.trim()) return;
    setCargando(true);
    setError("");
    setHistorial(null);
    try {
      setHistorial(await obtenerHistorial(codigo.trim()));
    } catch (err) {
      setError(err.message || "No se encontró el paquete.");
    } finally {
      setCargando(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Header titulo="Trazabilidad de Paquetes" subtitulo="Consulta la línea de tiempo de un pedido (CUS-35)" />

      <main className="flex-grow p-8 space-y-6">
        {/* Buscador */}
        <form onSubmit={buscar} className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm flex gap-3">
          <input
            value={codigo}
            onChange={(e) => setCodigo(e.target.value)}
            placeholder="Código del paquete (ej. PD-001)"
            className="flex-1 p-3 bg-slate-50 border border-slate-200 rounded-xl outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            disabled={cargando}
            className="bg-blue-600 text-white px-6 rounded-xl font-semibold hover:bg-blue-700 transition flex items-center gap-2 disabled:opacity-60"
          >
            {cargando ? <Loader2 className="animate-spin" size={18} /> : <Search size={18} />}
            Buscar
          </button>
        </form>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-2xl p-5 flex items-center gap-3 text-red-700">
            <AlertCircle size={22} /> {error}
          </div>
        )}

        {historial && (
          <div className="grid lg:grid-cols-3 gap-6">
            {/* Ficha del pedido */}
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-3">
              <div className="flex items-center gap-3">
                <div className="p-3 bg-blue-600 text-white rounded-xl"><Package size={22} /></div>
                <div>
                  <h2 className="font-bold text-slate-800">{historial.codigo}</h2>
                  <span className="text-xs px-2 py-1 rounded-full bg-blue-100 text-blue-700">
                    {historial.estado_actual}
                  </span>
                </div>
              </div>
              <Dato etiqueta="Cliente" valor={historial.cliente_origen} />
              <Dato etiqueta="Destino" valor={historial.direccion_destino} icono={MapPin} />
              <Dato etiqueta="Distrito" valor={historial.distrito || "-"} />
              <Dato etiqueta="Ruta asignada" valor={historial.ruta_asignada || "Sin asignar"} />
              {historial.motivo_fallo && <Dato etiqueta="Motivo de fallo" valor={historial.motivo_fallo} />}
              {historial.url_evidencia && (
                <a
                  href={historial.url_evidencia}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-block text-sm text-blue-600 hover:underline"
                >
                  Ver evidencia (POD)
                </a>
              )}
            </div>

            {/* Línea de tiempo */}
            <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
              <h2 className="font-bold text-slate-800 mb-5">Línea de tiempo</h2>
              {historial.eventos.length === 0 ? (
                <p className="text-slate-400">Este paquete aún no tiene eventos registrados.</p>
              ) : (
                <ol className="relative border-l-2 border-slate-100 ml-2 space-y-6">
                  {historial.eventos.map((ev, i) => (
                    <li key={i} className="ml-6">
                      <span className="absolute -left-[9px] w-4 h-4 rounded-full bg-blue-600 border-2 border-white" />
                      <p className="font-semibold text-slate-800">{ev.evento}</p>
                      <p className="text-sm text-slate-500">{ev.descripcion}</p>
                      <p className="text-xs text-slate-400 mt-1">
                        {ev.fecha ? new Date(ev.fecha).toLocaleString("es-PE") : "Sin fecha"}
                        {ev.realizado_por ? ` · ${ev.realizado_por}` : ""}
                      </p>
                    </li>
                  ))}
                </ol>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

function Dato({ etiqueta, valor, icono: Icono }) {
  return (
    <div className="flex items-start gap-2 text-sm">
      {Icono && <Icono size={16} className="text-slate-400 mt-0.5" />}
      <div>
        <p className="text-slate-400">{etiqueta}</p>
        <p className="text-slate-700 font-medium">{valor}</p>
      </div>
    </div>
  );
}
