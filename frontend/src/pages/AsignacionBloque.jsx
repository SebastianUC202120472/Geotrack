import { useEffect, useState } from "react";
import { Truck, MapPin, User, Loader2, AlertCircle } from "lucide-react";
import Header from "../components/Header";
import { asignarBloquePedidos, getDistritos, getConductores } from "../services/api";

export default function AsignacionBloquePro() {
  const [distritos, setDistritos] = useState([]);
  const [conductores, setConductores] = useState([]);
  const [distrito, setDistrito] = useState("");
  const [conductor, setConductor] = useState("");
  const [nombreRuta, setNombreRuta] = useState("");
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        const [d, c] = await Promise.all([getDistritos(), getConductores()]);
        setDistritos(d.zonas_operativas || []);
        setConductores(Array.isArray(c) ? c : (c.vehiculos || []));
      } catch (err) {
        console.error("Error al cargar datos:", err);
      }
    };
    load();
  }, []);

  const generarPreview = () => {
    const zona = distritos.find((z) => z.distrito === distrito);
    const cond = conductores.find((c) => String(c.id) === String(conductor));
    if (!zona || !cond) return;
    setPreview({ distrito: zona.distrito, conductor: cond.nombre || cond.placa, pedidos: zona.total_pedidos });
  };

  const asignar = async () => {
    if (!distrito || !conductor || !nombreRuta) return alert("Completa todos los campos");
    setLoading(true);
    try {
      const res = await asignarBloquePedidos({ distrito, conductor_id: Number(conductor), nombre_ruta: nombreRuta });
      alert(`Ruta asignada: ${res.codigo || 'Correctamente'}`);
      setNombreRuta(""); setPreview(null);
    } catch (err) { alert(err.message); } finally { setLoading(false); }
  };

  return (
    // CAMBIO: Estructura flex para llenar toda la altura
    <div className="min-h-screen w-full bg-slate-50 flex flex-col">
      <Header />

      {/* CAMBIO: flex-grow permite que esta área se estire al máximo */}
      <main className="flex-grow w-full p-8">
        <div className="max-w-7xl mx-auto w-full h-full flex flex-col space-y-8">
          
          {/* Header de la sección */}
          <div className="bg-white p-8 rounded-3xl border border-slate-200 shadow-sm flex items-center gap-4">
            <div className="p-4 bg-blue-600 text-white rounded-2xl"><Truck size={28} /></div>
            <div>
              <h1 className="text-3xl font-extrabold text-slate-900">Asignación de Rutas</h1>
              <p className="text-slate-500">Configuración de bloques logísticos y asignación de flota.</p>
            </div>
          </div>

          {/* Grid que ocupa el espacio restante */}
          <div className="grid md:grid-cols-2 gap-8 flex-grow">
            
            {/* Formulario */}
            <div className="bg-white p-8 rounded-3xl border border-slate-200 shadow-sm space-y-6 flex flex-col">
              <input
                className="w-full p-4 bg-slate-50 border border-slate-200 rounded-2xl focus:ring-2 focus:ring-blue-500 outline-none"
                placeholder="Nombre de la nueva ruta"
                value={nombreRuta}
                onChange={(e) => setNombreRuta(e.target.value)}
              />

              <select className="w-full p-4 bg-slate-50 border border-slate-200 rounded-2xl outline-none" onChange={(e) => setDistrito(e.target.value)}>
                <option value="">Selecciona zona operativa</option>
                {distritos.map((d, i) => <option key={i} value={d.distrito}>{d.distrito} ({d.total_pedidos} pedidos)</option>)}
              </select>

              <select className="w-full p-4 bg-slate-50 border border-slate-200 rounded-2xl outline-none" onChange={(e) => setConductor(e.target.value)}>
                <option value="">Selecciona vehículo / conductor</option>
                {conductores.map((c) => <option key={c.id} value={c.id}>{c.placa || c.nombre}</option>)}
              </select>

              <div className="flex gap-4 mt-auto">
                <button onClick={generarPreview} className="flex-1 bg-slate-800 text-white p-4 rounded-2xl font-bold hover:bg-slate-900 transition">Vista previa</button>
                <button onClick={asignar} disabled={loading} className="flex-1 bg-blue-600 text-white p-4 rounded-2xl font-bold hover:bg-blue-700 transition shadow-lg shadow-blue-200 flex justify-center">
                  {loading ? <Loader2 className="animate-spin" /> : "Confirmar Asignación"}
                </button>
              </div>
            </div>

            {/* Panel de Vista Previa */}
            <div className="bg-white p-8 rounded-3xl border border-slate-200 shadow-sm flex flex-col">
              <h2 className="font-bold text-lg mb-6">Impacto Logístico</h2>
              {preview ? (
                <div className="space-y-6 flex-grow">
                  <div className="flex items-center gap-4 p-4 bg-slate-50 rounded-2xl">
                    <MapPin className="text-blue-600" /> <span>Zona: <b>{preview.distrito}</b></span>
                  </div>
                  <div className="flex items-center gap-4 p-4 bg-slate-50 rounded-2xl">
                    <User className="text-blue-600" /> <span>Conductor: <b>{preview.conductor}</b></span>
                  </div>
                  <div className="text-center py-6 border-t border-dashed mt-auto">
                    <p className="text-sm text-slate-400">Total de carga</p>
                    <p className="text-6xl font-extrabold text-blue-600 my-2">{preview.pedidos}</p>
                    <p className="text-slate-500">pedidos en este bloque</p>
                  </div>
                </div>
              ) : (
                <div className="flex-grow flex flex-col items-center justify-center text-slate-400 border-2 border-dashed rounded-2xl">
                  <AlertCircle className="mb-2 opacity-50" />
                  <p>Selecciona los parámetros y haz clic en Vista previa.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}